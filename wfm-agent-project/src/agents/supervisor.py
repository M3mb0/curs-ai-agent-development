import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from typing import TypedDict
from rag.search import search, cached_search
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY
from tools.wfm_data import load_wfm_data, get_daily_metrics, calculate_service_level
from google.genai.types import AutomaticFunctionCallingConfig


df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")


class State(TypedDict):
    question: str
    next_step: str
    tool_result: str
    final_answer: str
    iteration_count: int
    language: str
    lob: str
    date: str
    date2: str
    target_volume: int
    weekday: str
    offset_hours: int
    column_name: str


# --- LLM infrastructure ---

def route_by_complexity(task_type: str) -> str:
    """Selects the appropriate model name based on task complexity, for cost efficiency.

    Args:
        task_type: the type of task (e.g. "classification", "reasoning")

    Returns:
        The most cost-effective model name for the given task type
    """
    simple_tasks = ["classification", "routing", "extraction", "writing"]
    complex_tasks = ["analysis", "reasoning", "complex_writing"]

    if task_type in simple_tasks:
        return "gemini-3.5-flash-lite"
    elif task_type in complex_tasks:
        return "gemini-3.6-flash"
    return "gemini-3.5-flash-lite"


def get_llm(model_name: str) -> ChatGoogleGenerativeAI:
    """Creates an LLM client for the given model name, with automatic
    function calling explicitly disabled.

    Args:
        model_name: the Gemini model name to use

    Returns:
        A configured ChatGoogleGenerativeAI instance
    """
    llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=GEMINI_API_KEY)
    return llm.bind(automatic_function_calling=AutomaticFunctionCallingConfig(disable=True))


def call_llm(system_prompt: str, user_message: str, task_type: str = "reasoning") -> str:
    """Calls the LLM with a given system prompt and message, choosing
    the model based on task complexity.

    Args:
        system_prompt: instructions defining the task
        user_message: the content to process
        task_type: complexity category, used to pick the model

    Returns:
        The generated text response
    """
    model_name = route_by_complexity(task_type)
    llm = get_llm(model_name)
    full_prompt = f"{system_prompt}\n\nInput: {user_message}"
    response = llm.invoke(full_prompt)
    if isinstance(response.content, list):
        return response.content[0]["text"]
    return response.content


# --- Nodes ---

def rag_node(state: State) -> dict:
    """Searches the knowledge base and formats the results as text.

    Args:
        state: the current graph state, containing the question

    Returns:
        A dict with the "tool_result" key, containing the combined
        text from the top matching chunks
    """
    results = cached_search(state["question"])
    
    combined_text = ""
    for text, source, chunk_index, distance in results:
        combined_text += f"{text}\n\n"
    
    return {"tool_result": combined_text}


def extract_wfm_params_node(state: State) -> dict:
    """Extracts and normalizes all WFM query parameters from the user's
    question using the LLM, handling ambiguous or malformed input.

    Args:
        state: the current graph state, containing the question

    Returns:
        A dict with keys for language, lob, date, date2, target_volume,
        weekday, offset_hours, and column_name (each "none" if not
        present in the question)
    """
    system_prompt = (
        "Extract and normalize all arguments needed for a WFM query from the question.\n\n"
        "Valid values:\n"
        "- language: Language 1, Language 2, Language 3, Language 4, Language 5, Language 6\n"
        "- lob: LOB 1, LOB 2, LOB 3, LOB 4\n"
        "- date, date2: format YYYY-MM-DD\n"
        "- target_volume: an integer number of calls\n"
        "- weekday: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday\n"
        "- offset_hours: an integer, can be negative\n"
        "- column_name: a short label for a new column\n\n"
        "Correct any typos or informal phrasing to match the valid formats above. "
        "Convert any date format to YYYY-MM-DD.\n\n"
        "Respond ONLY in this exact format, with all 8 keys present:\n"
        "language=...;lob=...;date=...;date2=...;target_volume=...;weekday=...;offset_hours=...;column_name=...\n\n"
        "If an argument is not present in the question, write none for that key.\n\n"
        "Example: language=Language 1;lob=LOB 1;date=2015-10-20;date2=none;"
        "target_volume=none;weekday=none;offset_hours=none;column_name=none"
    )

    response = call_llm(system_prompt, state["question"], task_type="extraction")

    parts = response.strip().split(";")
    params = {}
    for part in parts:
        key, value = part.split("=")
        params[key] = value

    return params


def wfm_metrics_node(state: State) -> dict:
    """Retrieves daily call metrics and formats them as text.

    Args:
        state: the current graph state, containing language, lob, and date

    Returns:
        A dict with the "tool_result" key, containing the formatted metrics
    """
    metrics = get_daily_metrics(df, state["language"], state["lob"], state["date"])
    
    combined_text = ""
    for key, value in metrics.items():
        combined_text += f"{key}: {value}\n"
    
    return {"tool_result": combined_text}


def service_level_node(state: State) -> dict:
    """Retrieves service level and abandon rate metrics, formatted as text.

    Args:
        state: the current graph state, containing language, lob, and date

    Returns:
        A dict with the "tool_result" key, containing the formatted metrics
    """
    result = calculate_service_level(df, state["language"], state["lob"], state["date"])

    combined_text = ""
    for key, value in result.items():
        combined_text += f"{key}: {value}\n"

    return {"tool_result": combined_text}


def supervisor_node(state: State) -> dict:
    """Decides which specialist should act next, based on current state.

    Args:
        state: the current graph state

    Returns:
        A dict with the "next_step" and "iteration_count" keys
    """
    system_prompt = (
        "You are a supervisor coordinating: "
        "rag (searches company procedures/knowledge base), "
        "extractor (extracts query parameters from a WFM-related question), "
        "metrics (retrieves call metrics: offered, handled, abandoned), "
        "service_level (retrieves service level % and abandon rate %), "
        "done (task complete, ready to answer).\n\n"
        "If the question is about company procedures or definitions, choose rag. "
        "If the question is about WFM data and the parameters have NOT been "
        "extracted yet, choose extractor. "
        "If parameters are already extracted and the question is about raw "
        "call counts (offered, handled, abandoned), choose metrics. "
        "If parameters are already extracted and the question is about "
        "service level or abandon rate percentages, choose service_level. "
        "If you already have a tool result, choose done.\n\n"
        "Respond with EXACTLY ONE WORD: rag, extractor, metrics, service_level, or done."
    )

    context = f"Question: {state['question']}\n"
    context += f"Language: {state.get('language', 'none')}\n"
    context += f"LOB: {state.get('lob', 'none')}\n"
    context += f"Date: {state.get('date', 'none')}\n"
    context += f"Date2: {state.get('date2', 'none')}\n"
    context += f"Target volume: {state.get('target_volume', 'none')}\n"
    context += f"Weekday: {state.get('weekday', 'none')}\n"
    context += f"Offset hours: {state.get('offset_hours', 'none')}\n"
    context += f"Column name: {state.get('column_name', 'none')}\n"
    context += f"Tool result so far: {state.get('tool_result', 'none')}\n"

    decision = call_llm(system_prompt, context, task_type="routing").strip().lower()

    current_count = state.get("iteration_count", 0)
    new_count = current_count + 1

    if new_count >= 10:
        decision = "done"

    # print(f"[DEBUG] Turn {new_count}: decision={decision}, language={state.get('language', 'none')}")
    return {"next_step": decision, "iteration_count": new_count}


def route_from_supervisor(state: State) -> str:
    """Reads the supervisor's decision and returns the matching node name.

    Args:
        state: the current graph state, containing next_step

    Returns:
        The name of the next node
    """
    return state["next_step"]


def format_answer_node(state: State) -> dict:
    """Formulates a clear, professional answer based on the tool result.

    Args:
        state: the current graph state, containing question and all
            normalized parameters, plus tool_result

    Returns:
        A dict with the "final_answer" key
    """
    system_prompt = (
    "You are a helpful assistant. Based on the tool result provided, "
    "write a clear, concise answer to the user's original question "
    "and offer a suggestion if it is the case. "
    "Use the normalized Language and LOB values provided below, "
    "not the possibly misspelled ones from the original question."
    )
    
    context = f"Question: {state['question']}\n"
    context += f"Language: {state.get('language', 'none')}\n"
    context += f"LOB: {state.get('lob', 'none')}\n"
    context += f"Date: {state.get('date', 'none')}\n"
    context += f"Date2: {state.get('date2', 'none')}\n"
    context += f"Target volume: {state.get('target_volume', 'none')}\n"
    context += f"Weekday: {state.get('weekday', 'none')}\n"
    context += f"Offset hours: {state.get('offset_hours', 'none')}\n"
    context += f"Column name: {state.get('column_name', 'none')}\n"
    context += f"Tool result: {state['tool_result']}"

    answer = call_llm(system_prompt, context, task_type="writing")

    return {"final_answer": answer}


if __name__ == "__main__":
    # Test 1: clear question
    test_state1 = {"question": "How many calls for Language 1 on LOB 1, on 2015-10-20?"}
    print(extract_wfm_params_node(test_state1))
    
    # Test 2: ambiguous question with typo
    test_state2 = {"question": "How many calls for Lang tow on lob 1, on Oct 20?"}
    print(extract_wfm_params_node(test_state2))

    test_state = {"language": "Language 1", "lob": "LOB 1", "date": "2015-10-20"}
    print(wfm_metrics_node(test_state))

    workflow = StateGraph(State)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("metrics", wfm_metrics_node)
    workflow.add_node("service_level", service_level_node)
    workflow.add_node("extractor", extract_wfm_params_node)
    workflow.add_node("writer", format_answer_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_edge("rag", "supervisor")
    workflow.add_edge("metrics", "supervisor")
    workflow.add_edge("service_level", "supervisor")
    workflow.add_edge("extractor", "supervisor")
    workflow.add_edge("writer", END)

    workflow.add_conditional_edges("supervisor", route_from_supervisor, {
        "rag": "rag",
        "extractor": "extractor",
        "metrics": "metrics",
        "service_level": "service_level",
        "done": "writer"
    })

    graph = workflow.compile()

    # result = graph.invoke({"question": "How many calls for Language 1 on LOB 1, on 2015-10-20?"})
    # print("\nFinal result:")
    # print(result)

    result = graph.invoke({"question": "What's the service level for Lungage tow on lob 3, on 2015-10-20?"})
    print(result)