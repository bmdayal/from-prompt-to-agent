"""
The Lab 4 team of agents (Planner, Researcher, Critic, Writer) as one importable module.
Used by scripts/plan_my_day.py. The notebook builds the same thing step by step.
"""
import json

from . import llm
from .agent import run_agent
from .tools import check_conflicts, search_sessions

PLANNER_SYSTEM = """You are the PLANNER for a conference assistant.
Read the attendee's request and extract the day they attend and their interests, most important first.
Reply ONLY with JSON: {"day": "Thursday" or "Friday" or "Saturday", "topics": ["short topic words, e.g. agents, security, healthcare"]}"""

CRITIC_SYSTEM = """You are the CRITIC. You review a draft conference agenda.
The CONFLICT REPORT was computed by code and is always correct.
For each conflict, remove the session whose topic is LOWER in the INTEREST ORDER.
Reply ONLY with JSON: {"approved": true or false, "issues": ["short descriptions"], "remove": ["session ids to remove"]}"""

WRITER_SYSTEM = """You are the WRITER.
Turn the AGENDA into a short, friendly message for a conference attendee.
List each session on its own line as: start time, title, room.
Use only the sessions in the AGENDA. End with one practical tip. Keep it under 120 words."""


def planner(request):
    plan = llm.parse_json(llm.ask(request, system=PLANNER_SYSTEM, json_mode=True))
    if not isinstance(plan, dict) or not plan.get("topics"):
        plan = {"day": "Thursday", "topics": ["agents"]}
    plan["topics"] = [t.lower() for t in plan["topics"]][:4]
    return plan


def researcher(topic, day, use_llm=True):
    if not use_llm:
        return search_sessions(topic, day)
    _, messages = run_agent(f"Search the program for {topic} sessions on {day} and list their ids.", verbose=False)
    found = []
    for m in messages:
        if m["role"] == "user" and m["content"].startswith("Observation:"):
            data = llm.parse_json(m["content"].split(":", 1)[1])
            items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
            found += [s for s in items if isinstance(s, dict) and "id" in s and "title" in s]
    return found


def critic(draft, interests):
    report = check_conflicts([s["id"] for s in draft])
    prompt = (f"INTEREST ORDER: {json.dumps(interests)}\n"
              f"DRAFT: {json.dumps(draft)}\n"
              f"CONFLICT REPORT: {json.dumps(report)}")
    verdict = llm.parse_json(llm.ask(prompt, system=CRITIC_SYSTEM, json_mode=True)) or {}
    return report, verdict


def writer(agenda):
    return llm.ask(f"AGENDA: {json.dumps(agenda)}", system=WRITER_SYSTEM)


def plan_my_day(request, use_llm_researcher=True, verbose=True):
    plan = planner(request)
    if verbose:
        print("Planner:", plan)
    draft = []
    for topic in plan["topics"]:
        for s in researcher(topic, plan["day"], use_llm_researcher):
            if s["id"] not in [d["id"] for d in draft]:
                draft.append({**{k: s[k] for k in ("id", "title", "start", "end", "room")}, "topic": topic})
    draft.sort(key=lambda s: s["start"])
    if verbose:
        print("Researcher found:", [s["id"] for s in draft])
    for _ in range(3):
        report, verdict = critic(draft, plan["topics"])
        if report["ok"]:
            break
        ids = {s["id"] for s in draft}
        remove = [i for i in verdict.get("remove", []) if i in ids] or [report["conflicts"][0]["b"]]
        draft = [s for s in draft if s["id"] not in remove]
    if verbose:
        print("Critic approved:", [s["id"] for s in draft], "\n")
    return writer(draft)
