"""
The agent loop you build by hand in Lab 3, saved here so Labs 4 and 5 can reuse it.

    question -> THINK (ask the LLM) -> ACT (run a tool) -> OBSERVE (read the result) -> repeat
"""
import json

from . import llm
from .tools import TOOLS, describe_tools, run_tool

AGENT_RULES = """You are the iGET Conference Concierge, an AI agent that helps attendees.
You can use these tools:
{tools}

Reply with ONE JSON object and nothing else, in this exact shape:
{{"thought": "your short reasoning", "action": "<tool name or final_answer>", "args": {{...}}}}

Rules:
- To use a tool, set "action" to the tool name and put its arguments in "args".
- When you know the answer, use "action": "final_answer" with "args": {{"answer": "..."}}.
- Only state facts that came from tool results. If the tools found nothing, say so. Never invent sessions, rooms or times.
- Use one tool per reply. You will see the result as an "Observation"."""


def agent_system_prompt(tools=TOOLS):
    return AGENT_RULES.format(tools=describe_tools(tools))


def show(step, kind, text):
    icons = {"think": "THINK  ", "act": "ACT    ", "observe": "OBSERVE", "answer": "ANSWER ", "warn": "WARNING"}
    text = text if len(text) < 400 else text[:400] + " ..."
    print(f"[step {step}] {icons.get(kind, kind)} | {text}")


def run_agent(question, tools=TOOLS, history=None, max_steps=6, ask_fn=None, verbose=True):
    """
    Run the agent until it gives a final answer or hits max_steps.
    history: a list of earlier messages (this is the agent's short-term MEMORY).
    ask_fn: swap in a different brain (Lab 5 uses this to simulate failures).
    Returns (answer, messages).
    """
    ask_fn = ask_fn or llm.ask
    system = agent_system_prompt(tools)
    messages = list(history or []) + [{"role": "user", "content": question}]

    for step in range(1, max_steps + 1):
        reply = ask_fn(messages, system=system, json_mode=True)
        messages.append({"role": "assistant", "content": reply})
        decision = llm.parse_json(reply)

        if not isinstance(decision, dict) or "action" not in decision:
            if verbose:
                show(step, "warn", f"Reply was not valid JSON, asking again: {reply[:80]!r}")
            messages.append({"role": "user", "content": "Observation: your last reply was not valid JSON. "
                             "Reply again with exactly one JSON object in the required shape."})
            continue

        if verbose and decision.get("thought"):
            show(step, "think", decision["thought"])

        if decision["action"] == "final_answer":
            answer = (decision.get("args") or {}).get("answer", "")
            if verbose:
                show(step, "answer", answer)
            return answer, messages

        if verbose:
            show(step, "act", f'{decision["action"]}({json.dumps(decision.get("args", {}))})')
        result = run_tool(tools, decision["action"], decision.get("args", {}))
        observation = json.dumps(result, default=str)
        if verbose:
            show(step, "observe", observation)
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    answer = "I stopped because I reached the step limit without a confident answer."
    if verbose:
        show(max_steps, "warn", answer)
    return answer, messages
