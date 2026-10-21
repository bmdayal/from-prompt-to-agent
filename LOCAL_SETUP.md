# Running the workshop on your own computer

You need about 15 minutes. These steps work on Windows, macOS and Linux.

## 1. Install Python
Download Python 3.10 or newer from https://www.python.org/downloads/.
**Windows:** on the first installer screen, tick **"Add python.exe to PATH"**.

Check it worked by opening a terminal (Windows: *Command Prompt* or *PowerShell*; macOS: *Terminal*):
```bash
python --version        # macOS/Linux may need: python3 --version
```

## 2. Download the workshop
Either click **Code > Download ZIP** on the GitHub page and unzip it, or use git:
```bash
git clone https://github.com/bmdayal/from-prompt-to-agent.git
cd from-prompt-to-agent
```

## 3. Create a virtual environment (a private space for this project's libraries)
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```
Your prompt now starts with `(.venv)`. Run the activate line again each time you open a new terminal.

## 4. Install the libraries
```bash
pip install -r requirements.txt
```

## 5. Add your API key (optional)
Copy `.env.example` to a new file named `.env` and replace the placeholder with your OpenAI key
(and optionally a Gemini key as a backup). A Gemini key on its own works too.
Skip this step to use the offline mock brain, or see [OFFLINE.md](OFFLINE.md) for a real local model.

## 6. Open the notebooks
**Option A, Jupyter in the browser:**
```bash
jupyter lab
```
Then open the `notebooks` folder and start with `00_setup.ipynb`.

**Option B, VS Code:** install VS Code and its *Python* and *Jupyter* extensions, open the
`from-prompt-to-agent` folder, open a notebook, and choose the `.venv` interpreter when asked
to "Select Kernel".

## 7. Or skip notebooks entirely
```bash
python scripts/concierge_chat.py
python scripts/plan_my_day.py "Thursday, agents and healthcare"
```
