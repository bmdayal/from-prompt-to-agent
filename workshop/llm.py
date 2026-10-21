"""
One small function, ask(), that talks to whichever "brain" is available:

  - "openai" : OpenAI models through an API key (needs a few dollars of prepaid credit)
  - "gemini" : Google Gemini through a free AI Studio API key
  - "ollama" : a model running on your own computer (no key, no internet needed)
  - "mock"   : a fake, rule-based brain built into this workshop, so every cell
               still runs with no key and no internet. Great for practice.

Order of preference: OpenAI, then Gemini, then Ollama, then mock. If you add BOTH an
OpenAI and a Gemini key, the second one automatically backs up the first.
You never need to edit this file for the workshop.
"""
import json
import logging
import os
import re
import sys
import time

# ------------------------------------------------------------------ settings
# Models are tried in order. If one is unavailable to your key, or hits its DAILY limit,
# the next one takes over. Override with the OPENAI_MODELS / GEMINI_MODELS environment
# variables, or in a notebook with e.g.  llm.OPENAI_MODELS = ["your-model-id"]
OPENAI_MODELS = os.environ.get("OPENAI_MODELS", "gpt-6-luna,gpt-5-mini,gpt-4o-mini").split(",")
OPENAI_REASONING_EFFORT = "low"   # small, fast reasoning; dropped automatically if a model rejects it
GEMINI_MODELS = os.environ.get("GEMINI_MODELS", "gemini-flash-latest,gemini-flash-lite-latest").split(",")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OPENAI_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Minimum seconds between calls, so we stay under per-minute limits instead of bursting.
PACE_SECONDS = {"openai": 0.5, "gemini": 4.0, "ollama": 0.0, "mock": 0.0}
MAX_WAIT_SECONDS = 60       # longest single wait for a per-minute limit to clear
RETRIES = 3                 # attempts per model before moving on

# If every real brain fails (no wifi, limits, outage), use the mock instead of crashing.
# Set False to see the real errors.
FALLBACK_TO_MOCK = True

KEY_NAMES = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}
PROVIDER_ORDER = ("openai", "gemini")

_state = {"provider": None, "backups": [], "client": None, "calls": 0, "fell_back": 0,
          "model_index": {"openai": 0, "gemini": 0}, "dropped_params": set(), "last_call": 0.0}


class ProviderError(Exception):
    def __init__(self, message, status=None, retry_after=None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after


# ----------------------------------------------------------------- key lookup
def _real(key):
    """Ignore empty values and the placeholder from .env.example."""
    return key if key and "paste-your" not in key else None


def _find_key(name):
    key = _real(os.environ.get(name))
    if key:
        return key
    if "google.colab" in sys.modules:  # Colab "Secrets" panel (the key icon)
        try:
            from google.colab import userdata
            return _real(userdata.get(name))
        except Exception:
            pass
    try:  # a .env file next to the notebooks, for running locally
        from dotenv import load_dotenv
        for path in (".env", "../.env"):
            if os.path.exists(path):
                load_dotenv(path)
        return _real(os.environ.get(name))
    except ImportError:
        return None


def _ollama_running():
    try:
        import requests
        return requests.get(OLLAMA_URL, timeout=1).ok
    except Exception:
        return False


def _available():
    found = [p for p in PROVIDER_ORDER if _find_key(KEY_NAMES[p])]
    if _ollama_running():
        found.append("ollama")
    return found


# --------------------------------------------------------------- configuration
def configure(provider="auto", verbose=True):
    """
    Pick the brain. "auto" = OpenAI if a key exists, else Gemini, else Ollama if running, else mock.
    Any other provider with a key becomes an automatic backup.
    """
    provider = os.environ.get("WORKSHOP_PROVIDER", provider or "auto").lower()
    available = [] if provider == "mock" else _available()

    if provider == "auto":
        provider = available[0] if available else "mock"
    elif provider != "mock" and provider not in available:
        what = KEY_NAMES.get(provider, "a running Ollama")
        print(f"'{provider}' is not available (no {what} found).", end=" ")
        provider = available[0] if available else "mock"
        print(f"Using '{provider}' instead.")

    if provider == "gemini" or "gemini" in available:
        _setup_gemini()
    _state["provider"] = provider
    _state["backups"] = [p for p in available if p != provider]
    if verbose:
        status()
    return provider


def _setup_gemini():
    if _state["client"] is not None:
        return
    try:
        from google import genai
    except ImportError:
        print("Installing the Gemini library (one time only)...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-genai"], check=False)
        from google import genai
    logging.getLogger("google_genai").setLevel(logging.ERROR)   # hide library chatter
    _state["client"] = genai.Client(api_key=_find_key("GEMINI_API_KEY"))


def _model(p):
    if p == "openai":
        return OPENAI_MODELS[min(_state["model_index"]["openai"], len(OPENAI_MODELS) - 1)]
    if p == "gemini":
        return GEMINI_MODELS[min(_state["model_index"]["gemini"], len(GEMINI_MODELS) - 1)]
    if p == "ollama":
        return OLLAMA_MODEL
    return "built-in practice brain"


def status():
    p = _state["provider"]
    line = f"Brain: {p}  |  model: {_model(p)}  |  calls so far: {_state['calls']}"
    if _state["backups"]:
        line += f"  |  backup: {', '.join(_state['backups'])}"
    if _state["fell_back"]:
        line += f"  |  mock fallbacks: {_state['fell_back']}"
    print(line)


def provider():
    return _state["provider"]


# ------------------------------------------------------------------- the API
def ask(prompt_or_messages, system=None, json_mode=False, temperature=0.0):
    """
    Send a prompt to the current brain and return its reply as text.

    prompt_or_messages: a string, or a list like
        [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    system: optional instructions that shape every answer
    json_mode: ask the model to reply with JSON only
    """
    if _state["provider"] is None:
        configure(verbose=False)
    messages = ([{"role": "user", "content": prompt_or_messages}]
                if isinstance(prompt_or_messages, str) else list(prompt_or_messages))
    _state["calls"] += 1

    chain = [_state["provider"]] + _state["backups"]
    for p in chain:
        if p == "mock":
            break
        reply = _ask_with_retries(p, messages, system, json_mode, temperature)
        if reply is not None:
            return reply
    if FALLBACK_TO_MOCK or _state["provider"] == "mock":
        if _state["provider"] != "mock":
            _state["fell_back"] += 1
            print("  (no real brain available right now, using the mock brain for this call)")
        return _mock_reply(messages, system, json_mode)
    raise RuntimeError("Every provider failed. Set llm.FALLBACK_TO_MOCK = True to keep going on the mock.")


def _ask_with_retries(p, messages, system, json_mode, temperature):
    """Try one provider. Waits out per-minute limits; moves to the next model on daily limits
    or when a model is not available to this key."""
    models = {"openai": OPENAI_MODELS, "gemini": GEMINI_MODELS}.get(p, [OLLAMA_MODEL])
    while True:
        attempt = 0
        while attempt < RETRIES:
            attempt += 1
            _pace(p)
            try:
                if p == "openai":
                    return _ask_openai(messages, system, json_mode)
                if p == "gemini":
                    return _ask_gemini(messages, system, json_mode, temperature)
                if p == "ollama":
                    return _ask_ollama(messages, system, json_mode, temperature)
            except Exception as e:
                kind, wait = _classify(e)
                if kind == "minute" and attempt < RETRIES:
                    print(f"  ({p} per-minute limit reached, waiting {wait:.0f}s, then retrying...)")
                    time.sleep(wait)
                    continue
                if kind == "transient" and attempt < RETRIES:
                    print(f"  ({p} is busy, waiting {wait:.0f}s, then retrying...)")
                    time.sleep(wait)
                    continue
                if kind == "param" and attempt < RETRIES:
                    continue  # an unsupported setting was dropped; try again right away
                if kind in ("daily", "model") and p in _state["model_index"] and _state["model_index"][p] < len(models) - 1:
                    old = _model(p)
                    _state["model_index"][p] += 1
                    why = "daily limit reached for" if kind == "daily" else "not available to this key:"
                    print(f"  ({p}: {why} {old}. Switching to {_model(p)}.)")
                    break  # restart the retry loop with the next model
                if kind == "model":
                    print(f"  ({p}: none of the models {models} are available to this key. "
                          f"Set llm.{p.upper()}_MODELS to a model your account can use. Details: {_short(e)})")
                    return None
                if kind == "auth":
                    print(f"  ({p}: the API key was rejected. Check that {KEY_NAMES.get(p, 'the key')} "
                          f"is copied correctly and still active. Details: {_short(e)})")
                elif kind == "billing":
                    print(f"  ({p}: billing problem, not a rate limit. This key's account or project has no "
                          f"credits left. Add credits, or use another key. Details: {_short(e)})")
                else:
                    print(f"  ({p} failed [{kind}]: {_short(e)})")
                return None
        else:
            return None


def _pace(p):
    gap = PACE_SECONDS.get(p, 0) - (time.time() - _state["last_call"])
    if gap > 0:
        time.sleep(gap)
    _state["last_call"] = time.time()


def _classify(e):
    """Turn an error into: billing, param (retry without a setting), model (switch model),
    minute (wait and retry), daily (switch model), transient, or fatal."""
    text = str(e)
    low = text.lower()
    status = getattr(e, "status", None)
    # 402 = billing problem (e.g. paid-tier project with no prepaid credits). Waiting won't help.
    if status == 402 or re.search(r"\b402\b", text) or any(w in low for w in (
            "prepayment credits", "credits are depleted", "credit_balance", "insufficient_quota",
            "billing account is disabled")):
        return "billing", 0
    is_429 = status == 429 or "429" in text or "resource_exhausted" in low or "rate limit" in low
    if status in (401, 403) or "invalid_api_key" in low or "api key not valid" in low:
        return "auth", 0
    if status == 400 and _drop_unsupported_param(low):
        return "param", 0
    if status == 404 or "model_not_found" in low or "does not exist" in low or ("model" in low and "not found" in low):
        return "model", 0
    if is_429:
        if any(w in low for w in ("perday", "per day", "(rpd)", "(tpd)", "limit: 0")):
            return "daily", 0
        return "minute", _retry_seconds(e, text)
    if status in (500, 502, 503) or any(w in text for w in ("503", "UNAVAILABLE", "overloaded")):
        return "transient", 5
    return "fatal", 0


def _retry_seconds(e, text):
    """Use the wait time the server suggests when it gives one, else a safe default."""
    if getattr(e, "retry_after", None):
        try:
            return min(float(e.retry_after) + 1, MAX_WAIT_SECONDS)
        except ValueError:
            pass
    m = re.search(r"(?:retry in|try again in|retryDelay['\"]?:\s*['\"]?)\s*(?:(\d+)m)?\s*([\d.]+)s", text)
    if m:
        secs = float(m.group(2)) + 60 * float(m.group(1) or 0)
        return min(secs + 1, MAX_WAIT_SECONDS)
    return 20


def _short(e):
    text = re.sub(r"\s+", " ", str(e))
    return text[:300] + (" ..." if len(text) > 300 else "")


# --------------------------------------------------------------- providers
def _drop_unsupported_param(low_error_text):
    """Reasoning models reject some settings. Remember which ones, so we stop sending them."""
    for param in ("reasoning_effort", "temperature", "response_format"):
        key = (_model("openai"), param)
        if param in low_error_text and key not in _state["dropped_params"]:
            _state["dropped_params"].add(key)
            return True
    return False


def _ask_openai(messages, system, json_mode):
    import requests
    if json_mode:  # ask for JSON in words; works for both JSON objects and lists
        system = (system or "") + "\n\nReply with valid JSON only. No extra text, no code fences."
    msgs = ([{"role": "system", "content": system}] if system else []) + messages
    body = {"model": _model("openai"), "messages": msgs}
    # Current OpenAI models reason before answering. "low" keeps them quick and cheap.
    # We do not send temperature: many reasoning models only accept the default.
    if OPENAI_REASONING_EFFORT and (body["model"], "reasoning_effort") not in _state["dropped_params"]:
        body["reasoning_effort"] = OPENAI_REASONING_EFFORT
    r = requests.post(f"{OPENAI_URL}/chat/completions",
                      headers={"Authorization": f"Bearer {_find_key('OPENAI_API_KEY')}"},
                      json=body, timeout=90)
    if r.status_code >= 400:
        raise ProviderError(f"{r.status_code} {r.text}", status=r.status_code,
                            retry_after=r.headers.get("retry-after"))
    return (r.json()["choices"][0]["message"]["content"] or "").strip()


def _ask_gemini(messages, system, json_mode, temperature):
    from google.genai import types
    contents = [{"role": "model" if m["role"] == "assistant" else "user",
                 "parts": [{"text": m["content"]}]} for m in messages]
    settings = dict(system_instruction=system, temperature=temperature,
                    response_mime_type="application/json" if json_mode else None)
    try:  # we use our own JSON tool protocol, so switch Google's function calling off
        settings["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)
        config = types.GenerateContentConfig(**settings)
    except Exception:
        settings.pop("automatic_function_calling", None)
        config = types.GenerateContentConfig(**settings)
    resp = _state["client"].models.generate_content(model=_model("gemini"), contents=contents, config=config)
    return (resp.text or "").strip()


def _ask_ollama(messages, system, json_mode, temperature):
    import requests
    msgs = ([{"role": "system", "content": system}] if system else []) + messages
    body = {"model": OLLAMA_MODEL, "messages": msgs, "stream": False, "options": {"temperature": temperature}}
    if json_mode:
        body["format"] = "json"
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


# ------------------------------------------------------------- JSON helper
def parse_json(text):
    """Pull the first JSON object or list out of a model reply. Returns None if impossible."""
    if text is None:
        return None
    text = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start, end = text.find(open_c), text.rfind(close_c)
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                continue
    return None


def _mock_reply(messages, system, json_mode):
    from .mock import MockBrain
    return MockBrain().reply(messages, system or "", json_mode)
