# Troubleshooting

**First, try this:** in Colab choose **Runtime > Restart session**, then run every cell from the top,
in order. It fixes most problems.

| What you see | What it means | Fix |
|---|---|---|
| `Brain: mock` but you added a key | The key was not found | In Colab, check the secret is named exactly `OPENAI_API_KEY` (or `GEMINI_API_KEY`), **Notebook access** is on, and you clicked **Grant access** when asked. Locally, check the file is named `.env` (not `.env.txt`). Then rerun the setup cell. |
| `NameError: name 'llm' is not defined` | The setup cell was not run | Run the setup cell (near the top) first. |
| `ModuleNotFoundError: No module named 'workshop'` | The helper files are missing | In Colab, rerun the setup cell (it downloads them). Locally, open the notebook from inside the repository folder. |
| `per-minute limit reached, waiting Ns` | APIs cap requests and tokens per minute (new OpenAI accounts and Gemini's free tier have low limits) | Normal. It waits as long as the server asks, then continues. In Lab 4 set `RESEARCHER_USES_LLM = False` to use fewer calls. |
| `daily limit reached for ... Switching to ...` | That model used up today's quota | Normal. It moves to the next model in the list, which has its own quota. Gemini's daily limits reset at midnight Pacific. |
| `not available to this key: ... Switching to ...` | Your account can't use that model (new, retired, or not enabled) | Normal. It tries the next model. If none work, see the `model not found` row below. |
| `billing problem, not a rate limit` (OpenAI `insufficient_quota`, or Gemini `402 ... prepayment credits are depleted`) | The account or project behind the key has no prepaid balance left | **OpenAI:** add credit under Settings > Billing at platform.openai.com. **Gemini:** add credit to that project, or create a key in a project with **no billing linked** (its Billing tier shows "Free" in AI Studio). |
| `the API key was rejected` (401, `invalid_api_key`, or `API key not valid`) | The key was copied incorrectly, deleted, or belongs to another service | Create a new key and update the Colab secret or `.env`. Check you didn't put an OpenAI key in `GEMINI_API_KEY` or the other way round. |
| `no real brain available right now, using the mock brain` | Every provider failed (network, limits, outage) | The cell still runs on the mock. Check your internet and keys, then rerun the setup cell. Set `llm.FALLBACK_TO_MOCK = False` to see the full error. |
| `none of the models ... are available to this key` | Every model in the list was renamed, retired or not enabled for your account | After the setup cell, run `llm.OPENAI_MODELS = ["model-id"]` with a model listed at platform.openai.com/docs/models (or `llm.GEMINI_MODELS = [...]` for Gemini), then rerun. |
| `413` or `Request too large` | One prompt is bigger than the per-minute token limit | Shorten the prompt, or start a fresh conversation (long memory grows every turn). |
| `git: command not found` or download fails in setup | No internet, or GitHub is blocked | Download the repository ZIP on another network and upload it to Colab's file panel, or run locally. |
| Agent repeats the same step until "step limit" | The loop never receives the tool result | Lab 3: complete TODO 2 (append the observation to `messages`). |
| `Reply was not valid JSON, asking again` | The model added extra text around the JSON | Normal. The loop asks again. If it happens every time, use a stronger model. |
| Answers differ from someone else's | LLMs are not fully deterministic, and brains differ | Expected. Compare which tools were called rather than exact wording. |
| `Connection refused` with Ollama | Ollama is not running | Start the Ollama app or run `ollama serve`. |
| Cells show `[*]` forever | A call is stuck or waiting | Click the stop button, then rerun the cell. Restart the session if needed. |

| Double-clicking a lab in Colab's **Files** panel opens it as a plain file | Notebooks downloaded by the setup cell aren't opened as runnable notebooks | Open every lab from its **Open in Colab** badge (in the README, Lab 0, or the end of each lab). |
| Your edits are gone after closing the tab | Notebooks opened from GitHub are temporary copies | Use **File > Save a copy in Drive** to keep your work. |

Still stuck? Open the matching notebook in the `solutions/` folder and copy the completed cell.
