import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from typing import TypedDict
from rag.search import search, cached_search
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GEMINI_API_KEY
from tools.wfm_data import (
    load_wfm_data,
    get_daily_metrics,
    calculate_service_level,
    get_talktime_by_period,
    compare_two_days,
    forecast_by_pattern,
    forecast_by_weekday_pattern,
    get_monthly_distribution_by_language,
    plot_language_distribution,
    add_timezone_column
)
from tools.capacity_planning import (
    load_arrival_pattern,
    SHIFTS,
    distribute_breaks_all_shifts,
    distribute_breaks_all_shifts_with_meetings,
    aggregate_breaks_by_interval,
    calculate_staffing,
    load_site_params,
    calculate_capacity,
)
from google.genai.types import AutomaticFunctionCallingConfig


df = load_wfm_data("wfm-agent-project/data/wfm.xlsx")
arrival_pattern = load_arrival_pattern("wfm-agent-project/data/wfm.xlsx")
site_params = load_site_params("wfm-agent-project/data/wfm.xlsx")


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
    meeting_times: str
    last_tool: str


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
    
    return {"tool_result": combined_text, "last_tool": "rag"}


def extract_wfm_params_node(state: State) -> dict:
    """Extracts and normalizes all WFM query parameters from the user's
    question using the LLM, handling ambiguous or malformed input.

    Args:
        state: the current graph state, containing the question

    Returns:
        A dict with keys for language, lob, date, date2, target_volume,
        weekday, offset_hours, column_name, and meeting_times (each "none"
        if not present in the question)
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
        "- meeting_times: comma-separated list of HH:MM-HH:MM ranges (24-hour "
        "format), e.g. 09:00-10:30,15:00-16:30. Convert casual time references "
        "intelligently: '9-10' with no AM/PM specified defaults to AM. Numbers "
        "13-23 are automatically PM. 'morning' means AM, 'afternoon'/'evening'/"
        "'night' means PM. Examples: '9 morning' = 09:00, '10 afternoon' = 22:00, "
        "'4-6 afternoon' = 16:00-18:00.\n"
        "- column_name: a short label for a new column\n\n"
        "Correct any typos or informal phrasing to match the valid formats above. "
        "Convert any date format to YYYY-MM-DD.\n\n"
        "Respond ONLY in this exact format, with all 9 keys present:\n"
        "language=...;lob=...;date=...;date2=...;target_volume=...;weekday=...;offset_hours=...;column_name=...;meeting_times=...\n\n"
        "If an argument is not present in the question, write none for that key.\n\n"
        "Example: language=Language 1;lob=LOB 1;date=2015-10-20;date2=none;"
        "target_volume=none;weekday=none;offset_hours=none;column_name=none;meeting_times=none"
    )
    print(f"[DEBUG] State language on entry: {state.get('language', 'MISSING')}")
    response = call_llm(system_prompt, state["question"], task_type="extraction")
    print(f"[DEBUG] Raw LLM response: {response}")

    parts = response.strip().split(";")
    params = {}
    for part in parts:
        key, value = part.split("=")
        if value == "none" and state.get(key):
            params[key] = state[key]
        else:
            params[key] = value
    params["tool_result"] = "none"

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
    
    return {"tool_result": combined_text, "last_tool": "metrics"}


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
    
    return {"tool_result": combined_text, "last_tool": "service_level"}


def talktime_node(state: State) -> dict:
    """Retrieves the total talk time for a period and formats it as text.

    Args:
        state: the current graph state, containing language, lob, date,
            and date2

    Returns:
        A dict with the "tool_result" key, containing the formatted metrics
    """
    result = get_talktime_by_period(df, state["language"], state["lob"], state["date"], state["date2"])

    combined_text = ""
    for key, value in result.items():
        combined_text += f"{key}: {value}\n"

    return {"tool_result": combined_text, "last_tool": "talktime"}


def compare_days_node(state: State) -> dict:
    """Compares WFM metrics between two days and formats the result as text.

    Args:
        state: the current graph state, containing language, lob, date,
            and date2

    Returns:
        A dict with the "tool_result" key, containing the comparison
    """
    result = compare_two_days(df, state["language"], state["lob"], state["date"], state["date2"])

    combined_text = ""
    for key, value in result.items():
        combined_text += f"{key}: {value}\n"

    return {"tool_result": combined_text, "last_tool": "compare_days"}


def forecast_node(state: State) -> dict:
    """Forecasts call volume distribution for a historical date, formatted as text.

    Args:
        state: the current graph state, containing language, lob, date,
            and target_volume

    Returns:
        A dict with the "tool_result" key, containing the forecast
    """
    target_volume = int(state["target_volume"])
    result = forecast_by_pattern(df, state["language"], state["lob"], state["date"], target_volume)

    combined_text = ""
    for key, value in result.items():
        combined_text += f"{key}: {value}\n"

    return {"tool_result": combined_text, "last_tool": "forecast"}


def forecast_weekday_node(state: State) -> dict:
    """Forecasts call volume distribution based on a weekday's pattern, formatted as text.

    Args:
        state: the current graph state, containing language, lob, weekday,
            and target_volume

    Returns:
        A dict with the "tool_result" key, containing the forecast
    """
    target_volume = int(state["target_volume"])
    result = forecast_by_weekday_pattern(df, state["language"], state["lob"], state["weekday"], target_volume)

    combined_text = ""
    for key, value in result.items():
        combined_text += f"{key}: {value}\n"

    return {"tool_result": combined_text, "last_tool": "forecast_weekday"}


def distribution_node(state: State) -> dict:
    """Calculates monthly call distribution by language, generates a
    chart, and formats the result as text.

    Args:
        state: the current graph state, containing lob

    Returns:
        A dict with the "tool_result" key, containing the distribution
        and a note about the saved chart
    """
    result = get_monthly_distribution_by_language(df, state["lob"])

    output_dir = Path(__file__).parent.parent.parent / "data"
    chart_path = str(output_dir / "language_distribution.png")
    plot_language_distribution(result, chart_path)

    combined_text = ""
    for key, value in result.items():
        combined_text += f"{key}: {value}%\n"
    combined_text += f"\nA chart has been saved to: {chart_path}"

    return {"tool_result": combined_text, "last_tool": "distribution"}


def timezone_node(state: State) -> dict:
    """Adds a timezone-shifted column and formats a sample as text.

    Args:
        state: the current graph state, containing offset_hours and
            column_name

    Returns:
        A dict with the "tool_result" key, containing a sample of the
        shifted times
    """
    offset_hours = int(state["offset_hours"])
    column_name = state["column_name"]

    updated_df = add_timezone_column(df, offset_hours, column_name)

    sample = updated_df[["Intvl_UTC", column_name]].drop_duplicates().head(10)

    combined_text = ""
    for _, row in sample.iterrows():
        combined_text += f"{row['Intvl_UTC']} -> {row[column_name]}\n"

    return {"tool_result": combined_text, "last_tool": "timezone"}


def breaks_node(state: State) -> dict:
    """Distributes break minutes across all shifts (without meeting
    exclusions) and formats the result as text, including call volume
    for context.

    Args:
        state: the current graph state (not used directly, breaks are
            calculated from the fixed shift schedule)

    Returns:
        A dict with the "tool_result" key, containing call volume and
        break allocation per interval
    """
    all_breaks = distribute_breaks_all_shifts(arrival_pattern, SHIFTS)
    aggregated = aggregate_breaks_by_interval(all_breaks)

    combined_text = ""
    for _, row in arrival_pattern.iterrows():
        hour_str = str(row["hour"])
        calls = row["offered_calls"]
        breaks = round(aggregated.get(hour_str, 0))
        combined_text += f"{hour_str}: {calls} calls offered, {breaks} agents on break\n"

    return {"tool_result": combined_text, "last_tool": "breaks"}


def breaks_with_meetings_node(state: State) -> dict:
    """Distributes break minutes across all shifts, excluding team
    meeting times, and formats the result as text, including call
    volume for context.

    Args:
        state: the current graph state, containing meeting_times (a
            string with comma-separated HH:MM-HH:MM ranges, or "none"
            for default meeting times)

    Returns:
        A dict with the "tool_result" key, containing call volume and
        break allocation per interval
    """
    meeting_str = state.get("meeting_times", "none")

    if meeting_str == "none":
        meetings = [("09:00", "10:30"), ("15:00", "16:30")]
    else:
        meetings = []
        for interval in meeting_str.split(","):
            start, end = interval.split("-")
            meetings.append((start, end))

    all_breaks = distribute_breaks_all_shifts_with_meetings(arrival_pattern, SHIFTS, meetings)
    aggregated = aggregate_breaks_by_interval(all_breaks)

    combined_text = ""
    for _, row in arrival_pattern.iterrows():
        hour_str = str(row["hour"])
        calls = row["offered_calls"]
        breaks = round(aggregated.get(hour_str, 0))
        combined_text += f"{hour_str}: {calls} calls offered, {breaks} agents on break\n"

    return {"tool_result": combined_text, "last_tool": "breaks_meetings"}


def capacity_node(state: State) -> dict:
    """Calculates capacity per interval based on staffing and site
    parameters, formatted as text with call volume for context.

    Args:
        state: the current graph state, containing optional meeting_times

    Returns:
        A dict with the "tool_result" key, containing call volume and
        capacity per interval
    """
    meeting_str = state.get("meeting_times", "none")

    if meeting_str == "none":
        staffing = calculate_staffing(arrival_pattern, SHIFTS)
    else:
        meetings = []
        for interval in meeting_str.split(","):
            start, end = interval.split("-")
            meetings.append((start, end))
        staffing = calculate_staffing(arrival_pattern, SHIFTS, meetings)

    capacity = calculate_capacity(staffing, site_params)

    combined_text = ""
    for _, row in arrival_pattern.iterrows():
        hour_str = str(row["hour"])
        calls = row["offered_calls"]
        cap = round(capacity.get(hour_str, 0), 2)
        combined_text += f"{hour_str}: {calls} calls offered, {cap} capacity\n"

    return {"tool_result": combined_text, "last_tool": "capacity"}


def supervisor_node(state: State) -> dict:
    """Decides which specialist should act next, based on current state.

    Uses a deterministic check first: if a tool that needs extracted
    parameters was already used and those parameters are present but
    no result exists yet for the current question, route directly to
    the same tool without asking the LLM (avoids unreliable LLM routing
    decisions on follow-up questions). Otherwise, falls back to
    LLM-based routing.

    Args:
        state: the current graph state

    Returns:
        A dict with the "next_step" and "iteration_count" keys
    """
    print(f"[DEBUG-SUPER] language={state.get('language', 'MISSING')}, lob={state.get('lob', 'MISSING')}")

    last_tool = state.get("last_tool", "none")
    lob = state.get("lob", "none")
    tool_result = state.get("tool_result", "none")
    current_count = state.get("iteration_count", 0)
    new_count = current_count + 1

    tools_needing_params = ["metrics", "service_level", "talktime", "compare_days",
                              "forecast", "forecast_weekday", "distribution", "timezone"]

    # Deterministic shortcut: if we already used a parameter-based tool
    # and the parameters are present, but no fresh result yet, go
    # straight to that same tool.
    if last_tool in tools_needing_params and lob != "none" and tool_result == "none":
        print(f"[DEBUG-SUPER] Deterministic route to: {last_tool}")
        return {"next_step": last_tool, "iteration_count": new_count}

    system_prompt = (
        "You are a supervisor coordinating: "
        "rag (searches company procedures/knowledge base), "
        "extractor (extracts query parameters from a WFM-related question), "
        "metrics (retrieves call metrics: offered, handled, abandoned), "
        "service_level (retrieves service level % and abandon rate %), "
        "talktime (retrieves total talk time for a date range), "
        "compare_days (retrieves comparison of WFM metrics between two days), "
        "forecast (retrieves the forecasted call volume), "
        "forecast_weekday (retrieves the forecasted call volume, based on a weekday, like Monday, Tuesday, etc), "
        "distribution (retrieves monthly call distribution percentage by language, with a chart), "
        "timezone (shifts call times by a given offset, e.g. UTC-4), "
        "breaks (distributes agent break times across the day, without meeting exclusions), "
        "breaks_meetings (distributes agent break times, excluding team meeting periods), "
        "capacity (calculates call-handling capacity per interval, based on staffing), "
        "done (task complete, ready to answer).\n\n"
        "If the question is about company procedures or definitions, choose rag. "
        "If the question is about WFM data and lob is still 'none', choose extractor. "
        "Note: fields like date, date2, target_volume, weekday, offset_hours, and "
        "column_name will naturally be 'none' if not relevant to the question "
        "- this is expected and does NOT mean extraction failed. Only lob is "
        "always required; other fields depend on the specific question type.\n"
        "For distribution questions, only LOB is needed - language and date "
        "being 'none' is expected and normal for this type of question. Once "
        "lob is extracted, proceed directly to distribution.\n"
        "Note: breaks and breaks_meetings questions do NOT strictly require "
        "language/lob/date - if the question mentions specific meeting times, "
        "extract those first (meeting_times field), then route to the "
        "appropriate breaks node. If NO parameters are extractable at all, "
        "skip extraction and route directly to breaks/breaks_meetings.\n"
        "If the question is about total talk time over a period, choose talktime. "
        "If parameters are already extracted and the question is about raw "
        "call counts (offered, handled, abandoned), choose metrics. "
        "If parameters are already extracted and the question is about "
        "service level or abandon rate percentages, choose service_level. "
        "If parameters are already extracted and the question compares two "
        "specific dates, choose compare_days. "
        "If parameters are already extracted and the question forecasts based on "
        "a specific historical DATE (e.g. '2015-10-20'), choose forecast. "
        "If parameters are already extracted and the question forecasts based on "
        "a WEEKDAY pattern (e.g. 'Monday'), choose forecast_weekday. "
        "If parameters are already extracted and the question asks about the "
        "percentage distribution of calls across languages, choose distribution. "
        "If parameters are already extracted and the question asks to convert "
        "or shift times to a different timezone/offset, choose timezone. "
        "If the question is about break distribution WITHOUT mentioning team "
        "meetings, choose breaks. "
        "If the question specifically mentions team meetings or asks to exclude "
        "meeting times from break planning, choose breaks_meetings. "
        "If the question is about capacity, call-handling capability, or how "
        "many calls can be handled per interval, choose capacity. "
        "Note: capacity questions do NOT strictly require language/lob/date - "
        "if meeting times are mentioned, extract those first, otherwise route "
        "directly to capacity.\n"
        "If you already have a tool result, choose done.\n\n"
        "Respond with EXACTLY ONE WORD: rag, extractor, metrics, service_level, talktime,"
        "compare_days, forecast, forecast_weekday, distribution, timezone, breaks, breaks_meetings, capacity or done."
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
    context += f"Tool result so far: {tool_result}\n"
    context += f"Last tool used: {last_tool}\n"

    decision = call_llm(system_prompt, context, task_type="routing").strip().lower()

    if new_count >= 10:
        decision = "done"

    print(f"[DEBUG-SUPER] LLM route to: {decision}")
    return {"next_step": decision, "iteration_count": new_count}


def route_from_supervisor(state: State) -> str:
    """Reads the supervisor's decision and returns the matching node name.

    Args:
        state: the current graph state, containing next_step

    Returns:
        The name of the next node
    """
    # print(f"[DEBUG] Routing decision: '{state['next_step']}'")
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
    "write a clear, concise answer to the user's original question. "
    "ALWAYS include a brief suggestion or insight, even if performance "
    "looks good (e.g., what to monitor, or confirmation that no action "
    "is needed). "
    "Use the normalized Language and LOB values provided below, "
    "not the possibly misspelled ones from the original question." 
    "If, the user wrotes a wrong word like, laguage, instead of language,  " 
    "when you answer please use the correct word"
    "If the tool result is about staffing or break distribution, explain "
    "clearly what the numbers mean and proactively flag any intervals where "
    "coverage seems low, suggesting additional staffing if relevant."
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
    context += f"Tool result: {state.get('tool_result', 'No tool result available.')}"

    answer = call_llm(system_prompt, context, task_type="writing")

    return {"final_answer": answer}


if __name__ == "__main__":
    # # Test 1: clear question
    # test_state1 = {"question": "How many calls for Language 1 on LOB 1, on 2015-10-20?"}
    # print(extract_wfm_params_node(test_state1))
    
    # # Test 2: ambiguous question with typo
    # test_state2 = {"question": "How many calls for Lang tow on lob 1, on Oct 20?"}
    # print(extract_wfm_params_node(test_state2))

    # test_state = {"language": "Language 1", "lob": "LOB 1", "date": "2015-10-20"}
    # print(wfm_metrics_node(test_state))

    workflow = StateGraph(State)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("metrics", wfm_metrics_node)
    workflow.add_node("service_level", service_level_node)
    workflow.add_node("talktime", talktime_node)
    workflow.add_node("compare_days", compare_days_node)
    workflow.add_node("forecast", forecast_node)
    workflow.add_node("forecast_weekday", forecast_weekday_node)
    workflow.add_node("distribution", distribution_node)
    workflow.add_node("timezone", timezone_node)
    workflow.add_node("breaks", breaks_node)
    workflow.add_node("breaks_meetings", breaks_with_meetings_node)
    workflow.add_node("capacity", capacity_node)
    workflow.add_node("extractor", extract_wfm_params_node)
    workflow.add_node("writer", format_answer_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_edge("rag", "supervisor")
    workflow.add_edge("metrics", "supervisor")
    workflow.add_edge("service_level", "supervisor")
    workflow.add_edge("talktime", "supervisor")
    workflow.add_edge("compare_days", "supervisor")
    workflow.add_edge("forecast", "supervisor")
    workflow.add_edge("forecast_weekday", "supervisor")
    workflow.add_edge("distribution", "supervisor")
    workflow.add_edge("timezone", "supervisor")
    workflow.add_edge("breaks", "supervisor")
    workflow.add_edge("breaks_meetings", "supervisor")
    workflow.add_edge("capacity", "supervisor")
    workflow.add_edge("extractor", "supervisor")
    workflow.add_edge("writer", END)

    workflow.add_conditional_edges("supervisor", route_from_supervisor, {
        "rag": "rag",
        "extractor": "extractor",
        "metrics": "metrics",
        "service_level": "service_level",
        "talktime": "talktime",
        "compare_days": "compare_days",
        "forecast": "forecast",
        "forecast_weekday": "forecast_weekday",
        "distribution": "distribution",
        "timezone": "timezone",
        "breaks": "breaks",
        "breaks_meetings": "breaks_meetings",
        "capacity": "capacity",
        "done": "writer"
    })

    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    # result = graph.invoke({"question": "How many calls for Language 1 on LOB 1, on 2015-10-20?"})
    # print("\nFinal result:")
    # print(result)

    # result = graph.invoke({"question": "What's the service level for Lungage tow on lob 3, on 2015-10-20?"})
    # print(result)

    # result = graph.invoke({"question": "What's the total talk time for Language 1 on LOB 1, between 2015-10-14 and 2015-10-20?"})
    # print(result)

    # result = graph.invoke({"question": "Compare Language 1 on LOB 1 between 2015-10-20 and 2015-10-21"})
    # print(result)

    # result = graph.invoke({"question": "Forecast 500 calls for Language 1 on LOB 1 based on 2015-10-20 pattern"})
    # print(result["final_answer"])

    # result = graph.invoke({"question": "Forecast 1200 calls for Language 2 on LOB 1 based on Monday pattern"})
    # print(result["final_answer"])

    # result = graph.invoke({"question": "What's the call distribution by language for LOB 2?"})
    # print(result["final_answer"])

    # result = graph.invoke({"question": "Show me the call times shifted by UTC-4, name the column utc_minus_4"})
    # print(result["final_answer"])

    # result1 = graph.invoke({"question": "How are breaks distributed, considering team meetings between 9-10 and 15-16?"})
    # print("Test 1:", result1["final_answer"])

    # result2 = graph.invoke({"question": "How are breaks distributed, with meetings from 9 morning to 10 morning and 4 to 6 afternoon?"})
    # print("Test 2:", result2["final_answer"])

    # result3 = graph.invoke({"question": "Show me the break schedule for all agents today"})
    # print("\nTest 3:", result3["final_answer"])

    # result = graph.invoke({"question": "What's our capacity to handle calls throughout the day?"})
    # print(result["final_answer"])

    # config = {"configurable": {"thread_id": "session-10"}}
    # result1 = graph.invoke({"question": "What's the service level for Language 1 on LOB 1, on 2015-10-20?"}, config=config)
    # print(result1["final_answer"])

    # result2 = graph.invoke({"question": "What about LOB 2 instead?", "iteration_count": 0}, config=config)
    # print(result2["final_answer"])

    # config_new = {"configurable": {"thread_id": "brand-new-session"}}
    # result_test = graph.invoke({"question": "What's the service level for Language 1 on LOB 2, on 2015-10-20?"}, config=config_new)
    # print(result_test["final_answer"])

    # config = {"configurable": {"thread_id": "session-12"}}
    # result1 = graph.invoke({"question": "How many calls were offered for Language 1 on LOB 1, on 2015-10-20?"}, config=config)
    # print(result1["final_answer"])

    # result2 = graph.invoke({"question": "What about 2015-10-21 instead?", "iteration_count": 0}, config=config)
    # print(result2["final_answer"])

    config = {"configurable": {"thread_id": "session-14"}}
    result1 = graph.invoke({"question": "What is the SLA target for LOB 1?"}, config=config)
    print(result1["final_answer"])

    result2 = graph.invoke({"question": "How many calls were offered for Language 1 on LOB 1, on 2015-10-20?", "iteration_count": 0}, config=config)
    print(result2["final_answer"])