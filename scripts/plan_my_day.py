"""
Run the Lab 4 team of agents (Planner, Researcher, Critic, Writer) from the terminal.

    python scripts/plan_my_day.py "I'm there on Friday and love agents and evaluation"
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from workshop import llm                        # noqa: E402
from workshop.multi_agent import plan_my_day    # noqa: E402

llm.configure("auto")
request = " ".join(sys.argv[1:]) or "I'm attending on Thursday. I'm interested in AI agents, security and healthcare."
print(f"Request: {request}\n")
print(plan_my_day(request))
