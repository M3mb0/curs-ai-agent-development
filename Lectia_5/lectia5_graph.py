# from typing import TypedDict
# from langgraph.graph import StateGraph, START, END
# from langchain_google_genai import ChatGoogleGenerativeAI
# from dotenv import load_dotenv
# import os

# load_dotenv()

# # 1. Definim STATE - ce date "curg" prin graf
# class State(TypedDict):
#     question: str
#     answer: str

# # 2. Definim modelul
# llm = ChatGoogleGenerativeAI(
#     model="gemini-3.6-flash",
#     google_api_key=os.getenv("GEMINI_API_KEY")
# )

# # 3. Definim un NODE - o funcție care primește state și returnează actualizări
# def answer_node(state: State) -> dict:
#     """Calls the LLM with the question from state and returns the answer.

#     Args:
#         state: the current graph state, containing the question

#     Returns:
#         A dict with the "answer" key, to be merged into the state
#     """
#     response = llm.invoke(state["question"])
    
#     # response.content poate fi string simplu SAU listă de blocuri, depinde de model
#     if isinstance(response.content, list):
#         text = response.content[0]["text"]
#     else:
#         text = response.content
    
#     return {"answer": text}

# # 4. Construim graful
# workflow = StateGraph(State)
# workflow.add_node("answer", answer_node)
# workflow.add_edge(START, "answer")
# workflow.add_edge("answer", END)

# graph = workflow.compile()

# # 5. Rulăm graful
# result = graph.invoke({"question": "What is an AI agent, in 2 sentences?"})
# print(result["answer"])

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

class State(TypedDict):
    question: str
    answer: str
    is_complaint: bool

llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

def check_complaint_node(state: State) -> dict:
    """Checks whether the question contains complaint-related keywords.

    Args:
        state: the current graph state, containing the question

    Returns:
        A dict with the "is_complaint" key (True/False)
    """
    complaint_words = ["angry", "complaint", "refund", "cancel", "unacceptable"]
    question_lower = state["question"].lower()
    is_complaint = any(word in question_lower for word in complaint_words)
    return {"is_complaint": is_complaint}

def normal_answer_node(state: State) -> dict:
    """Answers a normal question directly with the LLM.

    Args:
        state: the current graph state, containing the question

    Returns:
        A dict with the "answer" key
    """
    response = llm.invoke(state["question"])
    text = response.content[0]["text"] if isinstance(response.content, list) else response.content
    return {"answer": text}

def escalation_node(state: State) -> dict:
    """Handles a complaint by escalating it, with a fixed message.

    Args:
        state: the current graph state, containing the question

    Returns:
        A dict with the "answer" key, containing an escalation message
    """
    return {"answer": "This request has been escalated to a senior support agent."}

def route_decision(state: State) -> str:
    """Decides which node to go to next, based on whether it's a complaint.

    Args:
        state: the current graph state, containing is_complaint

    Returns:
        The name of the next node: "escalation" or "normal_answer"
    """
    if state["is_complaint"]:
        return "escalation"
    return "normal_answer"

workflow = StateGraph(State)
workflow.add_node("check_complaint", check_complaint_node)
workflow.add_node("normal_answer", normal_answer_node)
workflow.add_node("escalation", escalation_node)

workflow.add_edge(START, "check_complaint")
workflow.add_conditional_edges("check_complaint", route_decision)
workflow.add_edge("normal_answer", END)
workflow.add_edge("escalation", END)

graph = workflow.compile()

# Test 1: întrebare normală
result1 = graph.invoke({"question": "What is the capital of France?"})
print("Test 1:", result1["answer"])

# Test 2: plângere
result2 = graph.invoke({"question": "This is unacceptable, I want a refund immediately!"})
print("Test 2:", result2["answer"])