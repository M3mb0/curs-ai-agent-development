"""Tests for LLM error handling: mapping Gemini API status codes to
LLMUnavailableError / LLMConfigError in call_llm, and fail-closed
behavior of safe_process_question. No real API calls are made - the
LLM, the graph, and the guardrail calls are replaced with monkeypatch.
"""


import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))

import pytest
from google.genai.errors import ClientError, ServerError
from agents import supervisor
from exceptions.custom_errors import LLMUnavailableError, LLMConfigError


CONFIG = {"configurable": {"thread_id": "test-thread"}}


def make_api_error(status_code: int) -> Exception:
    """Builds the error LangChain raises for a failed Gemini call: a
    wrapper exception raised from the Google SDK error that carries
    the HTTP status code.

    Args:
        status_code: the HTTP status code to simulate

    Returns:
        An exception whose __cause__ is the Google SDK error
    """
    response_json = {"error": {"code": status_code, "message": "simulated", "status": "SIMULATED"}}
    if status_code >= 500:
        sdk_error = ServerError(status_code, response_json)
    else:
        sdk_error = ClientError(status_code, response_json)
    try:
        raise RuntimeError(f"Error calling model ({status_code})") from sdk_error
    except RuntimeError as wrapper:
        return wrapper


class FailingLLM:
    """Fake LLM whose invoke always raises the given error."""

    def __init__(self, error: Exception):
        self.error = error

    def invoke(self, prompt):
        raise self.error


class FakeGraph:
    """Fake graph that returns a fixed answer and records if it was called."""

    def __init__(self):
        self.called = False

    def invoke(self, state, config=None):
        self.called = True
        return {"final_answer": "Service level is 85%."}


@pytest.fixture(autouse=True)
def reset_rate_limit(monkeypatch):
    """Gives each test an empty rate-limit history."""
    monkeypatch.setattr(supervisor, "_user_requests", {})


@pytest.mark.parametrize("status_code", [429, 503])
def test_call_llm_raises_unavailable_on_temporary_errors(monkeypatch, status_code):
    """Tests that temporary API errors (429, 503) become LLMUnavailableError."""
    monkeypatch.setattr(supervisor, "get_llm", lambda model_name: FailingLLM(make_api_error(status_code)))

    with pytest.raises(LLMUnavailableError):
        supervisor.call_llm("system", "question", task_type="classification")


@pytest.mark.parametrize("status_code", [400, 401, 403, 404])
def test_call_llm_raises_config_error_on_permanent_errors(monkeypatch, status_code):
    """Tests that permanent API errors (400, 401, 403, 404) become LLMConfigError."""
    monkeypatch.setattr(supervisor, "get_llm", lambda model_name: FailingLLM(make_api_error(status_code)))

    with pytest.raises(LLMConfigError):
        supervisor.call_llm("system", "question", task_type="classification")


def test_call_llm_reraises_errors_without_status_code(monkeypatch):
    """Tests that errors without an HTTP status code are not hidden."""
    monkeypatch.setattr(supervisor, "get_llm", lambda model_name: FailingLLM(ValueError("unexpected")))

    with pytest.raises(ValueError):
        supervisor.call_llm("system", "question")


@pytest.mark.parametrize("error, expected_text", [
    (LLMUnavailableError("429"), "temporarily unavailable"),
    (LLMConfigError("404"), "configuration error, check model/API key"),
])
def test_safe_process_question_fails_closed_when_injection_check_fails(monkeypatch, error, expected_text):
    """Tests that if the prompt injection check fails, the question is
    not passed to the graph and an error message is returned.
    """
    def failing_call_llm(system_prompt, user_message, task_type="reasoning"):
        raise error

    fake_graph = FakeGraph()
    monkeypatch.setattr(supervisor, "call_llm", failing_call_llm)
    monkeypatch.setattr(supervisor, "graph", fake_graph)

    answer = supervisor.safe_process_question("What's the service level?", "test_user", CONFIG)

    assert expected_text in answer
    assert fake_graph.called is False


@pytest.mark.parametrize("error, expected_text", [
    (LLMUnavailableError("503"), "temporarily unavailable"),
    (LLMConfigError("401"), "configuration error, check model/API key"),
])
def test_safe_process_question_fails_closed_when_output_filter_fails(monkeypatch, error, expected_text):
    """Tests that if the output filter fails, the unfiltered answer is
    not returned.
    """
    def call_llm_failing_on_second_call(system_prompt, user_message, task_type="reasoning"):
        if "Service level is 85%" in user_message:
            raise error
        return "SAFE"

    monkeypatch.setattr(supervisor, "call_llm", call_llm_failing_on_second_call)
    monkeypatch.setattr(supervisor, "graph", FakeGraph())

    answer = supervisor.safe_process_question("What's the service level?", "test_user", CONFIG)

    assert expected_text in answer
    assert "85%" not in answer


def test_guardrails_use_classification_task_type(monkeypatch):
    """Tests that both LLM guardrails ask for the cheap classification
    model instead of the default reasoning model.
    """
    task_types = []

    def recording_call_llm(system_prompt, user_message, task_type="reasoning"):
        task_types.append(task_type)
        return "SAFE"

    monkeypatch.setattr(supervisor, "call_llm", recording_call_llm)
    monkeypatch.setattr(supervisor, "graph", FakeGraph())

    supervisor.safe_process_question("What's the service level?", "test_user", CONFIG)

    assert task_types == ["classification", "classification"]
