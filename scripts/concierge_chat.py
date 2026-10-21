"""
Chat with the iGET Conference Concierge agent in your terminal (with memory).

Run from the repository folder:
    python scripts/concierge_chat.py
Type 'quit' to stop, 'trace' to toggle the step-by-step trace.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from workshop import llm                    # noqa: E402
from workshop.agent import run_agent        # noqa: E402

llm.configure("auto")
print("iGET Conference Concierge. Ask about sessions, rooms, speakers or clashes. Type 'quit' to exit.\n")
history, verbose = [], True
while True:
    try:
        question = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if question.lower() in ("quit", "exit", "q"):
        break
    if question.lower() == "trace":
        verbose = not verbose
        print(f"(trace {'on' if verbose else 'off'})")
        continue
    if not question:
        continue
    answer, history = run_agent(question, history=history, verbose=verbose)
    print(f"\nConcierge: {answer}\n")
    history = history[-20:]   # keep memory short so calls stay fast and cheap
print("Goodbye!")
