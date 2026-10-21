from nb_part1 import md, code, badge, next_lab, SETUP, SETUP_MD

# ---------------------------------------------------------------- Lab 3
LOOP_EX = '''
from workshop.tools import TOOLS, run_tool
from workshop.agent import agent_system_prompt, show

SYSTEM = agent_system_prompt(TOOLS)

def my_agent(question, history=None, max_steps=6):
    messages = list(history or []) + [{"role": "user", "content": question}]

    for step in range(1, max_steps + 1):
        # 1. THINK: ask the model what to do next
        reply = llm.ask(messages, system=SYSTEM, json_mode=True)
        messages.append({"role": "assistant", "content": reply})
        decision = llm.parse_json(reply)
        if not decision or "action" not in decision:
            show(step, "warn", "Reply was not valid JSON, asking again")
            messages.append({"role": "user", "content": "Observation: reply with one valid JSON object."})
            continue
        show(step, "think", decision.get("thought", ""))

        # 2. DONE? If the model chose final_answer, we stop
        if decision["action"] == "final_answer":
            answer = decision.get("args", {}).get("answer", "")
            show(step, "answer", answer)
            return answer, messages

        # 3. ACT: run the tool the model chose
        show(step, "act", f'{decision["action"]}({decision.get("args", {})})')
        # TODO 1: run the tool.
        # Hint: result = run_tool(TOOLS, decision["action"], decision.get("args", {}))
        result = {"error": "TODO 1 is not done yet"}

        # 4. OBSERVE: give the result back to the model
        observation = json.dumps(result, default=str)
        show(step, "observe", observation)
        # TODO 2: add the observation to `messages` as a user message
        # Hint: messages.append({"role": "user", "content": "Observation: " + observation})

    return "I stopped because I reached the step limit.", messages
'''
LOOP_SOL = (LOOP_EX
    .replace('''        # TODO 1: run the tool.
        # Hint: result = run_tool(TOOLS, decision["action"], decision.get("args", {}))
        result = {"error": "TODO 1 is not done yet"}''',
             '''        result = run_tool(TOOLS, decision["action"], decision.get("args", {}))''')
    .replace('''        # TODO 2: add the observation to `messages` as a user message
        # Hint: messages.append({"role": "user", "content": "Observation: " + observation})''',
             '''        messages.append({"role": "user", "content": "Observation: " + observation})'''))
assert LOOP_EX != LOOP_SOL and "TODO" not in LOOP_SOL

LAB3 = [
md(f"""
# Lab 3: The Agent Loop and Memory
{badge("03_agent_loop_and_memory")}

In Lab 2 we ran one turn by hand: *think, act, observe*. An **agent** simply repeats that turn in a
**loop** until the job is done:

```
   question
      |
      v
  +--------+     +-------+     +---------+
  | THINK  | --> |  ACT  | --> | OBSERVE |
  | (LLM)  |     | (tool)|     | (result)|
  +--------+     +-------+     +---------+
      ^                             |
      +-------- repeat -------------+
      |
      v
  final answer   (or stop after max_steps)
```

That loop, plus tools, plus memory, is the core of almost every agent framework.
"""),
md(SETUP_MD),
code(SETUP),
md("""
## Build the loop
Read the code below from top to bottom: it is the diagram above, written in Python.
Two lines are missing. Fill in **TODO 1** and **TODO 2** (the hints show exactly what to type).

*What if you skip them?* Run it anyway and watch: the agent never sees a result, so it repeats
itself until `max_steps` stops it. That is a real bug in real agents.
"""),
code(LOOP_EX, LOOP_SOL),
md("""
## Run your agent
**Predict:** how many steps will it take? Which tools will it use?
"""),
code('''
answer, convo = my_agent("Where is the session about memory on Friday?")
'''),
md("""
Read the trace: the agent **searched**, noticed it needed a room, **looked up details**, and only
then **answered**. Nobody told it to use two tools. It decided step by step.

Try a question that needs a different tool:
"""),
code('''
answer, convo = my_agent("Do S04 and S05 clash?")
'''),
md("""
## Memory
Short-term memory is simply **the conversation so far** (the `messages` list).
Watch what happens to a follow-up question **without** memory:
"""),
code('''
answer, convo = my_agent("Which sessions about agents are on Thursday?")
print("\\n--- follow-up WITHOUT memory ---")
answer2, _ = my_agent("What about Friday?")
'''),
md("""
"What about Friday?" is meaningless on its own: the agent does not know we were talking about agents.
Now pass the earlier conversation as `history`:
"""),
code('''
print("--- follow-up WITH memory ---")
answer3, convo = my_agent("What about Friday?", history=convo)
'''),
md("""
**Memory is powerful but not free:**
- The history grows every turn, so each call gets slower and more expensive.
- It can carry private details forward. Decide what is worth remembering.
- **Long-term memory** (saved to a file or database between sessions) is the same idea, stored outside the conversation.

## Your turn
1. Ask your agent your own question about the program. Count the steps.
2. Change `max_steps` to `1` and ask a question that needs two tools. What happens?
"""),
code('''
answer, convo = my_agent("TODO: your question here")
''', '''
answer, convo = my_agent("Who is speaking at the session on hallucinations, and where is it?")
print("\\n--- with max_steps=1 ---")
answer, _ = my_agent("Who is speaking at the session on hallucinations, and where is it?", max_steps=1)
'''),
md("""
## Key takeaways
- **Agent = LLM + tools + a loop.** The LLM decides, the loop repeats, tools act.
- `max_steps` is a safety budget. Every agent needs a way to stop.
- **Memory** is the message history. Pass it along and the agent can handle follow-ups.

""" + next_lab("04_multi_agent", "Lab 4, A Team of Agents") + """
"""),
]

# ---------------------------------------------------------------- Lab 4
LAB4 = [
md(f"""
# Lab 4: A Team of Agents
{badge("04_multi_agent")}

Some jobs are easier for a **team** of focused agents than for one agent doing everything.
Our team will plan a personal conference day:

| Agent | Job | Uses an LLM? |
|---|---|---|
| **Planner** | Turns a request into a plan: which day, which topics | Yes |
| **Researcher** | Finds sessions for each topic (your Lab 3 agent!) | Yes, with tools |
| **Critic** | Checks the draft agenda for clashes and removes conflicts | Code checks facts, LLM judges |
| **Writer** | Turns the final agenda into a friendly message (your exercise) | Yes |

**A word of caution:** more agents means more calls, more cost and more places to go wrong.
Use a team only when the task naturally splits into roles.
"""),
md(SETUP_MD),
code(SETUP),
code('''
from workshop.agent import run_agent
from workshop.tools import check_conflicts, get_session_details

# Real models on a free tier allow only a few calls per minute.
# Set this to False to make the Researcher use the search tool directly (fewer AI calls).
RESEARCHER_USES_LLM = True
'''),
md("""
## Agent 1: the Planner
It reads a free-form request and returns a structured plan. We **validate** its output
before trusting it (a habit you will see again in Lab 5).
"""),
code('''
PLANNER_SYSTEM = """You are the PLANNER for a conference assistant.
Read the attendee's request and extract the day they attend and their interests, most important first.
Reply ONLY with JSON: {"day": "Thursday" or "Friday" or "Saturday", "topics": ["short topic words, e.g. agents, security, healthcare"]}"""

def planner(request):
    plan = llm.parse_json(llm.ask(request, system=PLANNER_SYSTEM, json_mode=True))
    if not isinstance(plan, dict) or not plan.get("topics"):
        print("  Planner reply was unusable, using a safe default plan.")
        plan = {"day": "Thursday", "topics": ["agents"]}
    plan["topics"] = [t.lower() for t in plan["topics"]][:4]
    return plan

request = "I'm attending on Thursday. I'm interested in AI agents, security and healthcare. Plan my day!"
plan = planner(request)
print("PLAN:", plan)
'''),
md("""
## Agent 2: the Researcher
For each topic, the Researcher runs the agent from Lab 3. Notice that we collect sessions from the
**tool results**, not from the model's prose: tool output is the source of truth.
"""),
code('''
def researcher(topic, day):
    if not RESEARCHER_USES_LLM:
        from workshop.tools import search_sessions
        return search_sessions(topic, day)
    _, messages = run_agent(f"Search the program for {topic} sessions on {day} and list their ids.", verbose=False)
    found = []
    for m in messages:
        if m["role"] == "user" and m["content"].startswith("Observation:"):
            data = llm.parse_json(m["content"].split(":", 1)[1])
            items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
            found += [s for s in items if isinstance(s, dict) and "id" in s and "title" in s]
    return found

draft = []
for topic in plan["topics"]:
    for s in researcher(topic, plan["day"]):
        if s["id"] not in [d["id"] for d in draft]:
            draft.append({"id": s["id"], "title": s["title"], "start": s["start"],
                          "end": s["end"], "room": s["room"], "topic": topic})
draft.sort(key=lambda s: s["start"])

print(f"DRAFT AGENDA ({len(draft)} sessions):")
for s in draft:
    print(f'  {s["id"]}  {s["start"]}-{s["end"]}  [{s["topic"]}]  {s["title"]}')
'''),
md("""
**Predict:** will this draft work for a real person? Look at the times.

## Agent 3: the Critic
Checking times is a job for **code**, which is never wrong about arithmetic. Deciding **which**
session to drop is a judgment call, so that part goes to the **LLM**. Then we verify the LLM's
suggestion before applying it.
"""),
code('''
CRITIC_SYSTEM = """You are the CRITIC. You review a draft conference agenda.
The CONFLICT REPORT was computed by code and is always correct.
For each conflict, remove the session whose topic is LOWER in the INTEREST ORDER.
Reply ONLY with JSON: {"approved": true or false, "issues": ["short descriptions"], "remove": ["session ids to remove"]}"""

def critic(draft, interests):
    report = check_conflicts([s["id"] for s in draft])        # facts, from code
    prompt = (f"INTEREST ORDER: {json.dumps(interests)}\\n"
              f"DRAFT: {json.dumps(draft)}\\n"
              f"CONFLICT REPORT: {json.dumps(report)}")
    verdict = llm.parse_json(llm.ask(prompt, system=CRITIC_SYSTEM, json_mode=True)) or {}
    return report, verdict

agenda = list(draft)
for round_no in range(1, 4):                                   # bounded, like max_steps
    report, verdict = critic(agenda, plan["topics"])
    print(f"Round {round_no}: {len(report['conflicts'])} conflict(s). Critic says: {verdict}")
    if report["ok"]:
        print("Approved: no conflicts left.")
        break
    ids_in_agenda = {s["id"] for s in agenda}
    to_remove = [i for i in verdict.get("remove", []) if i in ids_in_agenda]   # trust, but verify
    if not to_remove:                                                          # safety net
        to_remove = [report["conflicts"][0]["b"]]
        print("  Critic gave no usable suggestion, removing", to_remove, "by default.")
    agenda = [s for s in agenda if s["id"] not in to_remove]

print("\\nFINAL AGENDA:")
for s in agenda:
    print(f'  {s["start"]}-{s["end"]}  {s["title"]}  ({s["room"]})')
'''),
md("""
## Your turn: Agent 4, the Writer
Write the instructions (system prompt) for a **Writer** agent that turns the final agenda into a
short, friendly message for the attendee. Keep the first sentence `You are the WRITER.` as is.
"""),
code('''
WRITER_SYSTEM = """You are the WRITER.
TODO: describe the tone, length and format you want."""

def writer(agenda):
    return llm.ask(f"AGENDA: {json.dumps(agenda)}", system=WRITER_SYSTEM)

print(writer(agenda))
''', '''
WRITER_SYSTEM = """You are the WRITER.
Turn the AGENDA into a short, friendly message for a conference attendee.
List each session on its own line as: start time, title, room.
Use only the sessions in the AGENDA. End with one practical tip. Keep it under 120 words."""

def writer(agenda):
    return llm.ask(f"AGENDA: {json.dumps(agenda)}", system=WRITER_SYSTEM)

print(writer(agenda))
'''),
md("""
## The whole team in one function
This is an **orchestrator**: plain code that passes structured data from one agent to the next.
"""),
code('''
def plan_my_day(request):
    plan = planner(request)
    print("Planner:", plan)
    draft = []
    for topic in plan["topics"]:
        for s in researcher(topic, plan["day"]):
            if s["id"] not in [d["id"] for d in draft]:
                draft.append({**{k: s[k] for k in ("id", "title", "start", "end", "room")}, "topic": topic})
    draft.sort(key=lambda s: s["start"])
    print("Researcher found:", [s["id"] for s in draft])
    for _ in range(3):
        report, verdict = critic(draft, plan["topics"])
        if report["ok"]:
            break
        remove = [i for i in verdict.get("remove", []) if i in {s["id"] for s in draft}] or [report["conflicts"][0]["b"]]
        draft = [s for s in draft if s["id"] not in remove]
    print("Critic approved:", [s["id"] for s in draft], "\\n")
    return writer(draft)

print(plan_my_day("I'll be there Friday. I love anything about agents and evaluation, and a bit of security."))
'''),
md("""
**Vote:** which agent should we add next? A *Navigator* (walking time between rooms), a
*Networking* agent (who to meet), or a *Reminder* agent (calendar invites)?

## Key takeaways
- Give each agent **one focused job** and a short, clear prompt.
- Pass **structured data** (JSON) between agents, not long prose.
- Let **code check facts** and the **LLM handle judgment and language**.
- **Bound every loop**, and always verify an agent's output before acting on it.

""" + next_lab("05_break_it", "Lab 5, Break It (and Fix It)") + """
"""),
]
