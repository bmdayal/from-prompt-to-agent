REPO = "bmdayal/from-prompt-to-agent"

def md(text):
    return ("markdown", text.strip(), None)

def code(ex, sol=None):
    return ("code", ex.strip(), (sol or ex).strip())

COLAB = f"https://colab.research.google.com/github/{REPO}/blob/main"
BADGE_IMG = "https://colab.research.google.com/assets/colab-badge.svg"

# "{{FOLDER}}" becomes "notebooks" in the exercise version and "solutions" in the solution version.
def badge(name):
    return f"[![Open In Colab]({BADGE_IMG})]({COLAB}/{{{{FOLDER}}}}/{name}.ipynb)"

def next_lab(name, title):
    return (f"**Next: {title}.** [![Open In Colab]({BADGE_IMG})]({COLAB}/{{{{FOLDER}}}}/{name}.ipynb)\n\n"
            f"Click the badge to open the next lab in a new Colab tab, then run its setup cell first. "
            f"(Each lab is self-contained, so you can close this one.)")

LABS = [
    ("00_setup", "Lab 0: Welcome and Setup"),
    ("01_prompt_to_structured_output", "Lab 1: From Prompt to Structured Output"),
    ("02_tools", "Lab 2: Giving the Model Tools"),
    ("03_agent_loop_and_memory", "Lab 3: The Agent Loop and Memory"),
    ("04_multi_agent", "Lab 4: A Team of Agents"),
    ("05_break_it", "Lab 5: Break It (and Fix It)"),
]
LAB_INDEX = "| Lab | Open the exercise | Stuck? Open the solution |\n|---|---|---|\n" + "\n".join(
    f"| {title} | [![Open In Colab]({BADGE_IMG})]({COLAB}/notebooks/{name}.ipynb) "
    f"| [solution]({COLAB}/solutions/{name}.ipynb) |" for name, title in LABS)

SETUP = f'''
# SETUP: run this cell first. It is safe to run more than once.
import os, sys, subprocess
REPO_URL = "https://github.com/{REPO}"

if os.path.isdir("../workshop"):        # running locally from notebooks/ or solutions/
    sys.path.insert(0, "..")
elif os.path.isdir("workshop"):         # running from the repo folder
    sys.path.insert(0, ".")
else:                                   # running in Google Colab: download the workshop files
    if not os.path.isdir("from-prompt-to-agent"):
        print("Downloading workshop files...")
        subprocess.run(["git", "clone", "-q", REPO_URL], check=True)
    sys.path.insert(0, "from-prompt-to-agent")

import json
from workshop import llm

PROVIDER = "auto"   # "auto", "openai", "gemini", "ollama" or "mock" (offline practice brain)
llm.configure(PROVIDER)
'''

SETUP_MD = """
### Setup
Run the cell below. The last line tells you which **brain** is answering:
`openai` or `gemini` (real AI in the cloud), `ollama` (AI on your own computer) or `mock`
(offline practice brain). All of them work for every exercise in this workshop.

In Colab, the first time a notebook reads your key, a pop-up asks for permission:
click **Grant access**. Every lab asks once.
"""

# ---------------------------------------------------------------- Lab 0
LAB0 = [
md(f"""
# Lab 0: Welcome and Setup
{badge("00_setup")}

**From Prompt to Agent** | IEEE iGET 2026 workshop

In this lab you will:
1. Learn what a notebook is and how to run it
2. Connect your code to a real AI model with an API key (optional, but more fun)
3. Send your very first message to an AI model from code

**Stuck at any point?** Type **STUCK** in the meeting chat, with what you see. A moderator will help.

## How to move between labs
Each lab is a separate notebook. To open one, click its **Open in Colab** badge below
(or the badge at the end of the lab you just finished). It opens in a new browser tab.

**Tip:** the setup cell downloads the workshop files into Colab's **Files** panel. Don't
open the labs from there: double-clicking a notebook in the Files panel opens it as a plain
file, not as a notebook you can run. Always use the badges.

""" + LAB_INDEX + """
"""),
md("""
## What is a notebook?
A notebook is a document made of **cells**:
- **Text cells** (like this one) explain things.
- **Code cells** (gray boxes) contain Python code you can run.

**To run a code cell:** click inside it and press **Shift + Enter**, or click the play button on its left.

While a cell runs you see `[*]` or a spinning icon. When it finishes, its output appears below it.
Cells run **in the order you run them**, so always go top to bottom.

Try it now: run the cell below.
"""),
code('''
print("Hello, iGET 2026!")
2 + 2
'''),
md("""
### Your turn
Replace `"your name here"` with your name, then run the cell.
"""),
code('''
my_name = "your name here"
print(f"Welcome to the workshop, {my_name}!")
''', '''
my_name = "Ada"
print(f"Welcome to the workshop, {my_name}!")
'''),
md("""
## Get an API key (about 3 minutes)
An **API key** is like a password that lets your code talk to an AI model in the cloud.
You can use **OpenAI**, **Gemini**, or both. If you add both, OpenAI is used first and Gemini
becomes the automatic backup.

**Option A: OpenAI** (needs a few dollars of prepaid credit)
1. Open **https://platform.openai.com/api-keys** and sign in.
2. Click **Create new secret key** and copy it (it starts with `sk-`).
3. Your account needs a prepaid balance. The minimum top-up is $5, and this whole workshop uses a tiny fraction of that.

**Option B: Gemini** (free tier, no credit card)
1. Open **https://aistudio.google.com**, sign in, and click **Get API key**, then **Create API key**.
2. Use a project **without** billing linked, so you stay on the free tier.

**Add the key to Colab:** click the **key icon** in the left sidebar (Secrets), click **Add new secret**,
set the name to `OPENAI_API_KEY` (or `GEMINI_API_KEY`), paste the key as the value, and switch on
**Notebook access**. **On your own computer:** copy `.env.example` to `.env` and paste the key there.

**Keep your keys private.** Never paste them into a code cell, a screenshot, or a GitHub repo.

**No key, or the wifi is down?** No problem. The workshop automatically uses a built-in
**mock brain**, so every cell still runs.
"""),
md(SETUP_MD),
code(SETUP),
md("""
## Your first message to an AI model
`llm.ask()` sends text to the model and gives you its reply as text. That is all an LLM does:
**text in, text out.**
"""),
code('''
answer = llm.ask("Explain what an AI agent is to a 10 year old, in 3 sentences.")
print(answer)
'''),
md("""
### Your turn
Write your own prompt and run it. Ideas: ask for a haiku about conferences, or ask what an
"LLM" is. (The mock brain only understands workshop topics, so with mock, ask about agents.)
"""),
code('''
my_prompt = "Write your prompt here"
print(llm.ask(my_prompt))
''', '''
my_prompt = "In two sentences, what is the difference between a chatbot and an AI agent?"
print(llm.ask(my_prompt))
'''),
md("""
## Checkpoint
You are ready if:
- the setup cell printed a line starting with `Brain:`
- the model replied to your prompt

Type **DONE** in the meeting chat.

""" + next_lab("01_prompt_to_structured_output", "Lab 1, From Prompt to Structured Output") + """
"""),
]

# ---------------------------------------------------------------- Lab 1
LAB1 = [
md(f"""
# Lab 1: From Prompt to Structured Output
{badge("01_prompt_to_structured_output")}

An LLM predicts text. In this lab you will see three things:
1. What happens when you ask about facts the model does not have
2. How **grounding** (giving it the data) fixes that
3. How **structured output** (JSON) lets your code use the answer

Throughout the workshop we are building the **iGET Conference Concierge**, an assistant that
helps attendees find sessions. The program is sample data in `workshop/data/sessions.json`.
"""),
md(SETUP_MD),
code(SETUP),
md("""
## Experiment 1: Ask without any data
**Predict first:** the model has never seen our conference program. What will it say?
Shout out your guess, then run the cell.
"""),
code('''
question = "Which sessions about agents are on Thursday at the iGET 2026 conference?"
print(llm.ask(question))
'''),
md("""
**Discuss:** Did it admit it does not know, or did it confidently invent sessions, rooms and times?
Confident invention is called a **hallucination**. Remember the role-play: this is the LLM
answering without the Tool card.
"""),
md("""
## Experiment 2: Grounding, give the model the data
We paste the program into the prompt and tell the model to use **only** that data.
"""),
code('''
from workshop.tools import SESSIONS

keys = ["id", "title", "day", "start", "end", "room", "level", "tags"]
program = json.dumps([{k: s[k] for k in keys} for s in SESSIONS])
print(f"The program has {len(SESSIONS)} sessions, {len(program)} characters of text.")

grounded_prompt = f"""Answer using ONLY the sessions data below.
If the answer is not in the data, say you could not find it.

SESSIONS DATA:
{program}

QUESTION: {question}"""

print(llm.ask(grounded_prompt))
'''),
md("""
Much better. **But** pasting the whole program into every prompt does not scale: a real conference
has hundreds of sessions, every character costs time and money, and some data is private.
Keep that thought. In Lab 2, **tools** solve it.
"""),
md("""
## Experiment 3: Structured output
People like sentences. **Programs like JSON.** If we ask for JSON, our code can sort, filter
and display the answer, or pass it to another program.
"""),
code('''
json_prompt = grounded_prompt + """

Reply ONLY with a JSON list of objects with the keys "id", "title", "start" and "room"."""

raw = llm.ask(json_prompt, json_mode=True)
print("Raw reply from the model:")
print(raw)

sessions = llm.parse_json(raw) or []
if isinstance(sessions, dict):   # some models wrap the list, e.g. {"sessions": [...]}
    sessions = next((v for v in sessions.values() if isinstance(v, list)), [])
print("\\nThe same data, used by our code:")
for s in sessions:
    print(f"{s.get('start', '?'):6} | {s.get('room', '?'):15} | {s.get('title', '?')}")
'''),
md("""
**Why this matters for agents:** when an agent decides "call the search tool with topic = agents",
that decision is also structured output. JSON is the bridge **from prompt to agent**.
"""),
md("""
## Your turn
Write a prompt that returns **beginner-level sessions on Friday** as JSON with the keys
`"title"` and `"level"`. Use `program` for the data, like the example above.
"""),
code('''
my_prompt = f"""TODO: write your instructions here.

SESSIONS DATA:
{program}

QUESTION: TODO: write your question here"""

raw = llm.ask(my_prompt, json_mode=True)
print(llm.parse_json(raw))
''', '''
my_prompt = f"""Answer using ONLY the sessions data below.

SESSIONS DATA:
{program}

QUESTION: Which Beginner level sessions are on Friday?
Reply ONLY with a JSON list of objects with the keys "title" and "level"."""

raw = llm.ask(my_prompt, json_mode=True)
print(llm.parse_json(raw))
'''),
md("""
## Key takeaways
- An LLM predicts plausible text. Without data, plausible can mean **made up**.
- **Grounding** (giving the model the facts) makes answers trustworthy.
- **Structured output** (JSON) turns answers into something code can use.

""" + next_lab("02_tools", "Lab 2, Giving the Model Tools") + """
"""),
]

# ---------------------------------------------------------------- Lab 2
TOOLS_DEF = '''
from workshop.tools import SESSIONS

def search_sessions(topic="", day=""):
    """Find sessions whose title, tags or track mention a topic, optionally on one day."""
    results = []
    for s in SESSIONS:
        text = " ".join([s["title"], s["track"], " ".join(s["tags"])]).lower()
        if topic and topic.lower() not in text:
            continue
        if day and s["day"].lower() != day.lower():
            continue
        results.append({k: s[k] for k in ("id", "title", "day", "start", "end", "room")})
    return results

def get_session_details(session_id):
    """Return everything about one session, for example S04."""
    for s in SESSIONS:
        if s["id"] == session_id.upper():
            return s
    return {"error": f"No session with id {session_id}"}

# Try the tools ourselves first. No AI involved yet!
print(search_sessions("security"))
print(get_session_details("S04")["speaker"])
'''

LAB2 = [
md(f"""
# Lab 2: Giving the Model Tools
{badge("02_tools")}

An LLM cannot run code, browse your files or read your database. But it **can** write a request,
like the LLM volunteer in the role-play who wrote on a card: *"Tool, please search for agents sessions."*

The pattern:
1. We give the model a **menu of tools** (name + what it does)
2. The model **chooses** a tool and writes the arguments as JSON
3. **Our code runs the tool** (the model never runs anything itself)
4. We hand the **result** back to the model so it can answer
"""),
md(SETUP_MD),
code(SETUP),
md("""
## Step 1: A tool is just a Python function
Nothing magic here. These are ordinary functions that search our program data.
"""),
code(TOOLS_DEF),
md("""
## Step 2: The menu and the rules
The model only knows about a tool if we **describe** it. Good descriptions lead to good choices.
"""),
code('''
TOOLS = {
    "search_sessions": search_sessions,
    "get_session_details": get_session_details,
}

TOOL_MENU = """- search_sessions(topic, day): find sessions about a topic (e.g. "agents", "security") on an optional day ("Thursday", "Friday", "Saturday"). Either argument may be "".
- get_session_details(session_id): full details (speaker, room, time, description) for one session id like S04."""

def build_system(menu):
    return f"""You are the iGET Conference Concierge. You can use these tools:
{menu}

Reply with ONE JSON object and nothing else:
{{"thought": "your short reasoning", "action": "<tool name or final_answer>", "args": {{...}}}}
When you know the answer, use "action": "final_answer" with "args": {{"answer": "..."}}.
Only state facts that came from tool results."""

SYSTEM = build_system(TOOL_MENU)
print(SYSTEM)
'''),
md("""
## Step 3: Let the model choose
**Predict:** which tool will it pick for this question, and with which arguments?
"""),
code('''
question = "When is the session on prompt engineering?"

reply = llm.ask(question, system=SYSTEM, json_mode=True)
decision = llm.parse_json(reply)
print("The model decided:")
print(json.dumps(decision, indent=2))
'''),
md("""
## Step 4: Our code runs the tool
The model only **asked**. Now our program actually does the work.
"""),
code('''
if decision and decision.get("action") in TOOLS:
    tool = TOOLS[decision["action"]]
    result = tool(**decision.get("args", {}))
    print("Tool result:")
    print(json.dumps(result, indent=2))
else:
    result = {"error": "the model did not choose a valid tool"}
    print("The model did not pick a tool this time:", decision)
'''),
md("""
## Step 5: Give the result back
We add the model's request and the tool's result (an **Observation**) to the conversation,
then ask again.
"""),
code('''
messages = [
    {"role": "user", "content": question},
    {"role": "assistant", "content": reply},
    {"role": "user", "content": "Observation: " + json.dumps(result)},
]
decision2 = llm.parse_json(llm.ask(messages, system=SYSTEM, json_mode=True))

if decision2 and decision2.get("action") == "final_answer":
    print("FINAL ANSWER:", decision2["args"]["answer"])
else:
    print("The model wants ANOTHER tool:", json.dumps(decision2))
    print("Doing this by hand gets tedious... in Lab 3 a loop will do it for us.")
'''),
md("""
## Your turn: write a new tool
Write `find_by_speaker(name)`, which returns the sessions whose speaker name contains `name`.

*Hint:* loop over `SESSIONS` and check `name.lower() in s["speaker"].lower()`.
"""),
code('''
def find_by_speaker(name):
    """Find sessions given by a speaker (full or partial name)."""
    # TODO: return a list of the sessions whose speaker contains `name`
    return []

print(find_by_speaker("Martinez"))
''', '''
def find_by_speaker(name):
    """Find sessions given by a speaker (full or partial name)."""
    return [{"id": s["id"], "title": s["title"], "day": s["day"], "start": s["start"],
             "room": s["room"], "speaker": s["speaker"]}
            for s in SESSIONS if name.lower() in s["speaker"].lower()]

print(find_by_speaker("Martinez"))
'''),
md("""
Now add it to the menu so the model knows it exists, and test it.
"""),
code('''
TOOLS["find_by_speaker"] = find_by_speaker
SYSTEM2 = build_system(TOOL_MENU + "\\n- find_by_speaker(name): find sessions given by a speaker (full or partial name).")

question = "What is Sofia Martinez presenting?"
decision = llm.parse_json(llm.ask(question, system=SYSTEM2, json_mode=True))
print("The model decided:", decision)
if decision and decision.get("action") in TOOLS:
    print("Tool result:", TOOLS[decision["action"]](**decision["args"]))
'''),
md("""
**Stretch goal:** write `sessions_in_room(room)` and add it to the menu.

## Key takeaways
- The model **chooses**, your code **executes**. You stay in control of what is possible.
- Tool **descriptions** are prompts too. Vague descriptions cause wrong choices.
- Each step is still structured output (JSON) from Lab 1.

""" + next_lab("03_agent_loop_and_memory", "Lab 3, The Agent Loop and Memory") + """
"""),
]
