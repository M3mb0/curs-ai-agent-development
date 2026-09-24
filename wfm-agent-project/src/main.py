"""Entry point for running the WFM agent interactively, via a
command-line chat loop.
"""


import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from agents.supervisor import safe_process_question


def main():
    """Runs an interactive chat loop with the WFM agent, using a
    persistent conversation thread. Each question goes through the
    guardrails (rate limiting, input validation, prompt injection
    detection, output filtering). Errors are printed and the loop
    continues. Type 'exit' to quit.
    """
    config = {"configurable": {"thread_id": "my_session"}}
    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Have a nice day!")
            break
        try:
            answer = safe_process_question(user_input, "cli_user", config)
        except Exception as e:
            answer = f"Something went wrong while processing your question: {e}"
        print(answer)


if __name__ == "__main__":
    main()