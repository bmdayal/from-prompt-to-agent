"""
Tools for the iGET Conference Concierge.

A "tool" is just a normal Python function that the agent is allowed to call.
The LLM never runs code itself: it asks for a tool by name, and OUR code runs it.

These are the same tools you build in Lab 2, collected here so that
Labs 3, 4 and 5 can import them.
"""
import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "sessions.json"


def load_sessions():
    """Read the sample conference program from the JSON file."""
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)["sessions"]


SESSIONS = load_sessions()
KNOWN_IDS = {s["id"] for s in SESSIONS}
KNOWN_ROOMS = {s["room"] for s in SESSIONS}
DAYS = ["Thursday", "Friday", "Saturday"]


def _short(s):
    """A compact view of a session, so we don't flood the model with text."""
    return {k: s[k] for k in ("id", "title", "day", "start", "end", "room")}


def search_sessions(topic: str = "", day: str = "") -> list:
    """Find sessions whose title, tags or track mention a topic, optionally on one day."""
    topic = (topic or "").strip().lower()
    day = (day or "").strip().lower()
    results = []
    for s in SESSIONS:
        haystack = " ".join([s["title"], s["track"], " ".join(s["tags"])]).lower()
        if topic and topic not in haystack:
            continue
        if day and s["day"].lower() != day:
            continue
        results.append(_short(s))
    return results[:8]


def get_session_details(session_id: str) -> dict:
    """Return everything we know about one session, by its id (for example S04)."""
    session_id = (session_id or "").strip().upper()
    for s in SESSIONS:
        if s["id"] == session_id:
            return s
    return {"error": f"No session with id {session_id}"}


def _minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def check_conflicts(session_ids: list) -> dict:
    """Check whether any of the given sessions overlap in time."""
    if isinstance(session_ids, str):
        session_ids = [x.strip() for x in session_ids.split(",")]
    chosen = [s for s in SESSIONS if s["id"] in {i.strip().upper() for i in session_ids}]
    unknown = [i for i in session_ids if i.strip().upper() not in KNOWN_IDS]
    conflicts = []
    for i, a in enumerate(chosen):
        for b in chosen[i + 1:]:
            same_day = a["day"] == b["day"]
            overlap = _minutes(a["start"]) < _minutes(b["end"]) and _minutes(b["start"]) < _minutes(a["end"])
            if same_day and overlap:
                conflicts.append({"a": a["id"], "b": b["id"],
                                  "detail": f'{a["id"]} ({a["start"]}-{a["end"]}) overlaps {b["id"]} ({b["start"]}-{b["end"]}) on {a["day"]}'})
    return {"conflicts": conflicts, "unknown_ids": unknown, "ok": not conflicts and not unknown}


def find_by_speaker(name: str) -> list:
    """Find sessions by (part of) a speaker's name. This is the Lab 2 exercise solution."""
    name = (name or "").strip().lower()
    return [_short(s) | {"speaker": s["speaker"]} for s in SESSIONS if name and name in s["speaker"].lower()]


# The "tool registry": a menu of tools the agent may use.
TOOLS = {
    "search_sessions": search_sessions,
    "get_session_details": get_session_details,
    "check_conflicts": check_conflicts,
}

TOOL_DESCRIPTIONS = {
    "search_sessions": 'search_sessions(topic, day): find sessions about a topic (e.g. "agents", "security") on an optional day ("Thursday", "Friday", "Saturday"). Either argument may be "".',
    "get_session_details": "get_session_details(session_id): full details (speaker, room, time, description) for one session id like S04.",
    "check_conflicts": "check_conflicts(session_ids): given a list of session ids, report any that overlap in time.",
    "find_by_speaker": "find_by_speaker(name): find sessions given by a speaker (full or partial name).",
}


def describe_tools(tools: dict) -> str:
    """Turn the tool registry into text the LLM can read."""
    return "\n".join(f"- {TOOL_DESCRIPTIONS.get(name, name)}" for name in tools)


def run_tool(tools: dict, name: str, args: dict):
    """Safely run a tool chosen by the model. Errors become data, not crashes."""
    if name not in tools:
        return {"error": f"Unknown tool '{name}'. Available tools: {list(tools)}"}
    try:
        return tools[name](**(args or {}))
    except Exception as e:  # a tool failure should not crash the whole agent
        return {"error": f"{type(e).__name__}: {e}"}
