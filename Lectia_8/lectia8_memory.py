from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver


class State(TypedDict):
    messages: list


def add_message_node(state: State) -> dict:
    """Adds a new simulated message to the conversation history.

    Args:
        state: the current graph state, containing the messages list

    Returns:
        A dict with the "messages" key, containing the updated list
    """
    current_messages = state.get("messages", [])
    new_message = f"Message number {len(current_messages) + 1}"
    updated_messages = current_messages + [new_message]
    return {"messages": updated_messages}


workflow = StateGraph(State)
workflow.add_node("add_message", add_message_node)
workflow.add_edge(START, "add_message")
workflow.add_edge("add_message", END)

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "test-conversation-1"}}

    result1 = graph.invoke({}, config=config)
    print("După primul apel:", result1["messages"])

    result2 = graph.invoke({}, config=config)
    print("După al doilea apel:", result2["messages"])

    config2 = {"configurable": {"thread_id": "test-conversation-2"}}
    result3 = graph.invoke({}, config=config2)
    print("Conversație nouă, primul apel:", result3["messages"])