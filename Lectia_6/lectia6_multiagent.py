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

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
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


workflow = StateGraph(State)
workflow.add_node("extractor", extractor_node)
workflow.add_node("analyst", analyst_node)

workflow.add_edge(START, "extractor")
workflow.add_edge("extractor", "analyst")
workflow.add_edge("analyst", END)

graph = workflow.compile()

result = graph.invoke({
    "question": "Yesterday LOB 1 had 500 calls offered, only 380 handled, "
                "and abandon rate was 18%, much higher than the usual 3% target."
})

print("Extracted facts:", result["extracted_facts"])
print("\nFinal answer:", result["final_answer"])