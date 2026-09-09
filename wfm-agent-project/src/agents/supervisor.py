import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from typing import TypedDict
from rag.search import search, cached_search
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY


class State(TypedDict):
    question: str
    next_step: str
    tool_result: str
    final_answer: str
    iteration_count: int
    language: str
    lob: str
    date: str


# --- LLM infrastructure ---

def route_by_complexity(task_type: str) -> str:
    """Selects the appropriate model name based on task complexity, for cost efficiency.

    Args:
        task_type: the type of task (e.g. "classification", "reasoning")

    Returns:
        The most cost-effective model name for the given task type
    """
    simple_tasks = ["classification", "routing", "extraction"]
    complex_tasks = ["analysis", "reasoning", "writing"]

    if task_type in simple_tasks:
        return "gemini-3.5-flash-lite"
    elif task_type in complex_tasks:
        return "gemini-3.6-flash"
    return "gemini-3.5-flash-lite"


def get_llm(model_name: str) -> ChatGoogleGenerativeAI:
    """Creates an LLM client for the given model name.

    Args:
        model_name: the Gemini model name to use

    Returns:
        A configured ChatGoogleGenerativeAI instance
    """
    return ChatGoogleGenerativeAI(model=model_name, google_api_key=GEMINI_API_KEY)


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
    """..."""
    system_prompt = (
    "Extract and NORMALIZE the language, LOB, and date from the question. "
    "Valid languages are: Language 1, Language 2, Language 3, Language 4, Language 5, Language 6. "
    "Valid LOBs are: LOB 1, LOB 2, LOB 3, LOB 4. "
    "Correct any typos or informal phrasing to match these exact formats. "
    "Convert any date format to YYYY-MM-DD. "
    "Respond ONLY in this exact format: language|lob|date "
    "Example: Language 1|LOB 1|2015-10-20 "
    "If any value is unclear or cannot be confidently normalized, respond with exactly: UNCLEAR"
    )
    response = call_llm(system_prompt, state["question"], task_type="extraction")
    
    if response.strip() == "UNCLEAR" or response.count("|") != 2:
        return {
            "tool_result": "I couldn't understand the date, language, or LOB. "
                          "Please specify clearly, e.g.: 'Language 1, LOB 1, 2015-10-20'."
        }
    
    language, lob, date = response.strip().split("|")
    return {"language": language, "lob": lob, "date": date}


if __name__ == "__main__":
    # Test 1: clear question
    test_state1 = {"question": "How many calls for Language 1 on LOB 1, on 2015-10-20?"}
    print(extract_wfm_params_node(test_state1))
    
    # Test 2: ambiguous question with typo
    test_state2 = {"question": "How many calls for Lang tow on lob 1, on Oct 20?"}
    print(extract_wfm_params_node(test_state2))