"""Entry point for running the WFM agent interactively, via a
command-line chat loop.
"""


import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from agents.supervisor import graph


def main():
    """Runs an interactive chat loop with the WFM agent, using a
    persistent conversation thread. Type 'exit' to quit.
    """
    config = {"configurable": {"thread_id": "my_session"}}
    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Have a nice day!")
            break
        result = graph.invoke({"question": user_input, "iteration_count": 0}, config=config)
        print(result["final_answer"])


if __name__ == "__main__":
    main()