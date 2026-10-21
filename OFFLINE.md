# Running without internet or an API key

## Option 1: the mock brain (zero setup)
If no key is found, the notebooks automatically use the built-in **mock brain**. You can also force it:
```python
PROVIDER = "mock"
```
The mock is a small rule-based program, not real AI. It understands the workshop questions
(sessions, rooms, speakers, clashes) and deliberately hallucinates when asked about the conference
without data, so every lesson still works. It cannot chat about other topics.

## Option 2: a real model on your computer with Ollama
Ollama runs open models locally. A laptop with 8 GB of RAM can run a small model.

1. Install Ollama from https://ollama.com.
2. Download a small model (about 2 GB, one time only, needs internet):
   ```bash
   ollama pull llama3.2
   ```
3. Make sure Ollama is running (it usually starts automatically; otherwise run `ollama serve`).
4. In the notebook setup cell set:
   ```python
   PROVIDER = "ollama"
   ```

To use a different model, set the environment variable `OLLAMA_MODEL` (for example `qwen2.5:3b`)
before starting Jupyter. Small local models follow the JSON format less reliably than Gemini.
That is a useful lesson in itself: watch how the agent loop recovers (and Lab 5 explains why).

Ollama does **not** work inside Google Colab, because Colab runs on Google's computers, not yours.
