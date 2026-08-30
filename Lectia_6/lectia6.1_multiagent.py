from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

class State(TypedDict):
    question: str
    extracted_facts: str
    final_answer: str
    next_step: str

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

def call_llm(system_prompt: str, user_message: str) -> str:
    """Calls the LLM with a given system prompt and user message.

    Args:
        system_prompt: instructions defining the agent's role and behavior
        user_message: the actual content to process

    Returns:
        The generated text response
    """
    full_prompt = f"{system_prompt}\n\nInput: {user_message}"
    response = llm.invoke(full_prompt)
    if isinstance(response.content, list):
        return response.content[0]["text"]
    return response.content


def extractor_node(state: State) -> dict:
    """Extracts key structured facts from the raw question/situation.

    Args:
        state: the current graph state, containing the question

    Returns:
        A dict with the "extracted_facts" key
    """
    system_prompt = (
        "You are a data extraction specialist. Extract only the key facts "
        "and numbers from the input, as a short bullet list. Do not interpret "
        "or give opinions, only extract what is explicitly stated."
    )
    facts = call_llm(system_prompt, state["question"])
    return {"extracted_facts": facts}


def analyst_node(state: State) -> dict:
    """Analyzes the extracted facts and produces a recommendation.

    Args:
        state: the current graph state, containing extracted_facts

    Returns:
        A dict with the "final_answer" key
    """
    system_prompt = (
        "You are a performance analyst. Based on the facts provided, "
        "identify the main issue and give one clear, actionable recommendation. "
        "Be concise, maximum 3 sentences."
    )
    analysis = call_llm(system_prompt, state["extracted_facts"])
    return {"final_answer": analysis}


def writer_node(state: State) -> dict:
    """Turns the analysis into a polished, professional message.

    Args:
        state: the current graph state, containing final_answer

    Returns:
        A dict with the "final_answer" key, rewritten professionally
    """
    system_prompt = (
        "You are a professional communications writer. Rewrite the input "
        "as a polished, professional message suitable for a team update email. "
        "Keep it concise, maximum 4 sentences."
    )
    polished = call_llm(system_prompt, state["final_answer"])
    return {"final_answer": polished}


def supervisor_node(state: State) -> dict:
    """Decides which specialist should act next, based on current state.

    Args:
        state: the current graph state

    Returns:
        A dict with the "next_step" key, naming the next node
    """
    system_prompt = (
        "You are a supervisor coordinating a team of specialists: "
        "extractor (extracts raw facts from a situation), "
        "analyst (analyzes facts and gives a recommendation), "
        "writer (polishes a message for professional communication), "
        "done (no more steps needed).\n\n"
        "Based on the current state, respond with EXACTLY ONE WORD: "
        "extractor, analyst, writer, or done."
    )
    
    context = f"Question: {state['question']}\n"
    context += f"Extracted facts so far: {state.get('extracted_facts', 'none')}\n"
    context += f"Analysis so far: {state.get('final_answer', 'none')}\n"
    
    decision = call_llm(system_prompt, context).strip().lower()
    return {"next_step": decision}


def route_from_supervisor(state: State) -> str:
    """Reads the supervisor's decision and returns the matching node name.

    Args:
        state: the current graph state, containing next_step

    Returns:
        The name of the next node
    """
    return state["next_step"]

workflow = StateGraph(State)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("extractor", extractor_node)
workflow.add_node("analyst", analyst_node)
workflow.add_node("writer", writer_node)

workflow.add_edge(START, "supervisor")
workflow.add_edge("extractor", "supervisor")   # <- se întoarce la supervisor!
workflow.add_edge("analyst", "supervisor")     # <- se întoarce la supervisor!
workflow.add_edge("writer", "supervisor")      # <- se întoarce la supervisor!
workflow.add_conditional_edges("supervisor", route_from_supervisor, {
    "extractor": "extractor",
    "analyst": "analyst",
    "writer": "writer",
    "done": END
})

graph = workflow.compile()

result = graph.invoke({
    "question": "Yesterday LOB 1 had 500 calls offered, only 380 handled, "
                "and abandon rate was 18%, much higher than the usual 3% target."
})
print(result["final_answer"])