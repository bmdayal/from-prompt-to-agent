# From Prompt to Agent

**A hands-on introduction to Agentic AI** | IEEE iGET 2026 workshop

Large Language Models are evolving from conversational assistants into agents that reason, use tools,
remember context and collaborate. In this workshop you build one step at a time, from a single prompt
to a small team of agents, using only your browser.

**No experience with AI, Python or notebooks needed.** If you can copy and paste, you can do this.

## The labs

Click a badge to open the lab in Google Colab (free, runs in your browser, nothing to install).
Each lab is its own notebook, so open them one at a time from this table, or from the
**Next** badge at the end of each lab. Run the setup cell at the top of every lab first.

Tip: the setup cell downloads the workshop files into Colab's **Files** panel. Don't open the labs
from there: a notebook double-clicked in the Files panel opens as a plain file you can't run.
Use the badges instead. To keep your changes, use **File > Save a copy in Drive**.

| Lab | What you build | Open | Stuck? |
|---|---|---|---|
| 0. Setup | Run your first notebook and talk to an AI model from code | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/notebooks/00_setup.ipynb) | [solution](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/solutions/00_setup.ipynb) |
| 1. Prompt to structured output | See hallucination, fix it with grounding, get JSON back | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/notebooks/01_prompt_to_structured_output.ipynb) | [solution](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/solutions/01_prompt_to_structured_output.ipynb) |
| 2. Tools | Let the model choose and call Python functions | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/notebooks/02_tools.ipynb) | [solution](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/solutions/02_tools.ipynb) |
| 3. Agent loop and memory | Build the think, act, observe loop and add memory | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/notebooks/03_agent_loop_and_memory.ipynb) | [solution](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/solutions/03_agent_loop_and_memory.ipynb) |
| 4. Multi-agent | A Planner, Researcher, Critic and Writer working as a team | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/notebooks/04_multi_agent.ipynb) | [solution](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/solutions/04_multi_agent.ipynb) |
| 5. Break it (and fix it) | Hallucinations, tool failures, bad output, runaway loops, prompt injection | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/notebooks/05_break_it.ipynb) | [solution](https://colab.research.google.com/github/bmdayal/from-prompt-to-agent/blob/main/solutions/05_break_it.ipynb) |

The running example is the **iGET Conference Concierge**, an assistant that finds sessions, checks for
time clashes and plans your day. The program in `workshop/data/sessions.json` is **fictional sample data**.

## Three ways to run it

| Option | Needs | Best for |
|---|---|---|
| **Google Colab** + an OpenAI or Gemini key | A browser and a Google account | The workshop itself |
| **Your own computer** | Python 3.10 or newer | Taking it home, see [LOCAL_SETUP.md](LOCAL_SETUP.md) |
| **Fully offline** | Ollama, or nothing at all | No internet, no key, see [OFFLINE.md](OFFLINE.md) |

Every notebook picks a "brain" automatically: **OpenAI** if it finds an OpenAI key, then **Gemini**,
then **Ollama** if one is running on your computer, otherwise the built-in **mock brain**. If you add both
an OpenAI and a Gemini key, Gemini takes over automatically when OpenAI fails. The mock is a simple rule-based
stand-in, so every cell runs even with no key and no internet. You can always see which brain answered
on the line that starts with `Brain:`.

## Getting an API key

You need one key, OpenAI or Gemini. Add both if you can: the second becomes an automatic backup.

**OpenAI (primary)**
1. Go to https://platform.openai.com/api-keys, sign in, and click **Create new secret key**. Copy it (it starts with `sk-`).
2. The OpenAI API is pay-as-you-go: your account needs a prepaid balance (the minimum top-up is $5). This workshop uses a tiny fraction of that.
3. In Colab: click the **key icon** on the left, add a secret named `OPENAI_API_KEY`, paste the key, and turn on notebook access.

**Gemini (free backup, no credit card)**
1. Go to https://aistudio.google.com, click **Get API key**, then **Create API key**. Use a project without billing linked to stay on the free tier.
2. Add it the same way as a secret named `GEMINI_API_KEY`.

On your own computer, copy `.env.example` to `.env` and paste your key(s) there instead.

Never put your key inside a notebook cell, a screenshot or a GitHub repository.
APIs have rate limits (requests and tokens per minute and per day). The code waits, switches to the next
model, or switches provider automatically when a limit is hit. Gemini's free tier may use your prompts to
improve Google's products, so do not send private or sensitive data.

## What is in this repository

```
notebooks/     the six labs, with small TODO exercises
solutions/     the same labs with every exercise completed (copy freely!)
workshop/      helper code: the LLM connection, mock brain, tools, agent loop, multi-agent team
scripts/       the same agents as plain Python programs for the terminal
tools_dev/     the script that generates notebooks/ and solutions/ (for maintainers)
```

## Try the terminal versions

```bash
python scripts/concierge_chat.py                      # chat with the agent (it remembers the conversation)
python scripts/plan_my_day.py "Friday, agents and security"   # run the team of agents
```

## Something not working?

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md). Most problems are a missing key, a rate limit,
or running cells out of order. When in doubt: **Runtime > Restart session**, then run from the top.

## Where to go next

Everything here is written in plain Python so you can see how agents really work. Agent frameworks
such as Strands Agents, Google ADK, LangGraph and CrewAI package the same loop, tools, memory and
multi-agent patterns with extra conveniences. Pick one and rebuild the Concierge in it.

---
Workshop by Brij Mohan for IEEE iGET 2026.
