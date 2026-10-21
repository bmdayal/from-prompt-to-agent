"""
The MOCK brain: a tiny rule-based imitation of an LLM.

It is NOT intelligent. It looks for keywords and follows simple rules, so that
every notebook cell runs even with no API key and no internet.
It also plays the "hallucinating chatbot" on purpose when asked about the
conference with no data, so you can see why grounding and tools matter.
"""
import json
import re

from .tools import SESSIONS, search_sessions, get_session_details, check_conflicts, find_by_speaker

DAY_WORDS = ["wednesday", "thursday", "friday", "saturday", "sunday"]
VOCAB = sorted({t for s in SESSIONS for t in s["tags"]} |
               {"multi-agent", "prompt", "hallucination", "memory", "orchestration", "tool", "privacy"},
               key=len, reverse=True)
VOCAB = [w for w in VOCAB if len(w) > 2]
SPEAKER_KEYS = {s["speaker"].replace("Dr. ", "").split()[-1].lower(): s["speaker"] for s in SESSIONS}


def _day(text):
    t = text.lower()
    for d in DAY_WORDS:
        if d in t:
            return d.capitalize()
    return ""


def _topics(text):
    t = text.lower()
    found = []
    for w in VOCAB:
        if re.search(rf"\b{re.escape(w)}", t) and not any(w in f for f in found):
            found.append(w)
    # map a few friendly words onto the data vocabulary
    if "hallucination" in found:
        found[found.index("hallucination")] = "hallucinations"
    if "tool" in found:
        found[found.index("tool")] = "tools"
    # keep the order the user mentioned them in (that is their priority)
    return sorted(found, key=lambda w: t.find(w.rstrip("s")))


def _unknown_topic(text):
    m = re.search(r"(?:session|talk|workshop)s? (?:on|about) ([a-z0-9 \-]+?)(?: on | this |\?|\.|$)", text.lower())
    return m.group(1).strip() if m else ""


def _speaker(text):
    t = text.lower()
    for key, full in SPEAKER_KEYS.items():
        if re.search(rf"\b{re.escape(key)}\b", t):
            return full
    return ""


def _fmt(s):
    return f'{s["id"]} "{s["title"]}" ({s["day"]} {s["start"]}-{s["end"]}, {s["room"]})'


def _act(thought, action, **args):
    return json.dumps({"thought": thought, "action": action, "args": args})


class MockBrain:
    def reply(self, messages, system, json_mode):
        sys_l = system.lower()
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if "you are the planner" in sys_l:
            return self._plan(last_user)
        if "you are the critic" in sys_l:
            return self._critique(last_user)
        if "you are the writer" in sys_l:
            return self._write(last_user)
        if '"action"' in system:
            return self._agent_step(messages, system)
        if json_mode or "json" in last_user.lower():
            return self._extract(last_user)
        return self._chat(last_user)

    # ------------------------------------------------------------ plain chat
    def _chat(self, text):
        t = text.lower()
        if "sessions data" in t:  # grounded: the data was pasted into the prompt
            q = t.split("question:")[-1] if "question:" in t else t
            hits = self._lookup(q)
            if not hits:
                return "Based on the program provided, I could not find a matching session."
            return "Based on the program provided:\n" + "\n".join(f"- {_fmt(s)}" for s in hits)
        if any(w in t for w in ("iget", "session", "conference", "keynote", "talk")):
            topic = (_topics(text) or [_unknown_topic(text) or "agentic AI"])[0]
            day = _day(text) or "Friday"
            # Deliberate, confident, made-up answer: this is what a hallucination looks like.
            return (f'Great question! The {topic.title()} session (S42) is on {day} at 2:00 PM in Hall Z, '
                    f'presented by Dr. Alan Reyes. It is one of the most popular talks at iGET 2026, '
                    f'so arrive 10 minutes early.')
        if "agent" in t:
            return ("An AI agent is like a helpful robot assistant. A normal chatbot can only talk. "
                    "An agent can also DO things: it thinks about your goal, picks a tool (like a "
                    "calculator or a search box), uses it, looks at the result, and keeps going until "
                    "the job is done. Think of it as a chatbot with hands and a to-do list.")
        return ("(Mock brain) I am the offline practice brain, so I only understand workshop "
                "questions about AI agents and the iGET program. Connect Gemini or Ollama for "
                "open-ended chat.")

    def _lookup(self, text):
        day = _day(text)
        topics = _topics(text)
        hits = []
        for topic in topics or [""]:
            for s in search_sessions(topic, day):
                if s not in hits:
                    hits.append(s)
        if not topics and not day:
            return []
        return hits

    # ------------------------------------------------- structured extraction
    def _extract(self, text):
        hits = self._lookup(text.lower().split("question:")[-1] if "question:" in text.lower() else text)
        return json.dumps([{"id": s["id"], "title": s["title"], "start": s["start"], "room": s["room"]} for s in hits])

    # ------------------------------------------------------- the agent loop
    def _agent_step(self, messages, system):
        # the current question is the last user message that is not a tool observation
        idx = max(i for i, m in enumerate(messages)
                  if m["role"] == "user" and not m["content"].startswith("Observation"))
        q = messages[idx]["content"]
        earlier = " ".join(m["content"] for m in messages[:idx]
                           if m["role"] == "user" and not m["content"].startswith("Observation"))
        steps = [m for m in messages[idx + 1:] if m["role"] == "assistant"]
        def _is_json(text):
            try:
                json.loads(text.split(":", 1)[-1])
                return True
            except Exception:
                return False
        # ignore "please reply with valid JSON" nudges: only real tool results count
        observations = [m["content"] for m in messages[idx + 1:]
                        if m["role"] == "user" and m["content"].startswith("Observation") and _is_json(m["content"])]
        ql = q.lower()
        topics = _topics(q) or _topics(earlier)
        topic = topics[0] if topics else (_unknown_topic(q) or _unknown_topic(earlier))
        day = _day(q) or _day(earlier)
        ids = re.findall(r"\bS\d{2}\b", q.upper())

        if not observations:
            speaker = _speaker(q)
            if speaker and "find_by_speaker" in system:
                return _act(f"The user asked about a speaker, so I will look up {speaker}.",
                            "find_by_speaker", name=speaker.replace("Dr. ", ""))
            if ids and any(w in ql for w in ("conflict", "clash", "overlap", "both")):
                return _act("I need to check these sessions for time overlaps.", "check_conflicts", session_ids=ids)
            if ids:
                return _act(f"I should get the details for {ids[0]}.", "get_session_details", session_id=ids[0])
            if not topic:
                return _act(f"No topic was given, so I will list sessions{' on ' + day if day else ''}.",
                            "search_sessions", topic="", day=day)
            return _act(f"I should search the program for '{topic}' sessions{' on ' + day if day else ''}.",
                        "search_sessions", topic=topic, day=day)

        last_obs = observations[-1].split(":", 1)[-1].strip()
        data = None
        try:
            data = json.loads(last_obs)
        except Exception:
            pass

        if isinstance(data, dict) and "error" in data:
            if len(steps) < 3 and "retry" not in "".join(s["content"] for s in steps):
                return _act("The tool failed. I will retry once.", json.loads(steps[-1]["content"])["action"],
                            **json.loads(steps[-1]["content"])["args"])
            return _act("The tool keeps failing, so I must say so honestly.", "final_answer",
                        answer=f"Sorry, I could not get that information because a tool failed ({data['error']}).")

        wants_details = any(w in ql for w in ("where", "room", "who", "speaker", "describe"))
        if isinstance(data, list) and data and wants_details and len(observations) == 1 and "id" in data[0]:
            return _act(f"I found a match. I will fetch full details for {data[0]['id']}.",
                        "get_session_details", session_id=data[0]["id"])

        return _act("I have what I need to answer.", "final_answer", answer=self._answer_from(data, topic, day))

    def _answer_from(self, data, topic, day):
        where = f" on {day}" if day else ""
        if isinstance(data, list):
            if not data:
                return f"I could not find any session about '{topic}'{where} in the iGET program."
            return f"Here is what I found{where}:\n" + "\n".join(
                f"- {_fmt(s)}" + (f', speaker {s["speaker"]}' if "speaker" in s else "") for s in data)
        if isinstance(data, dict) and "conflicts" in data:
            if data["ok"]:
                return "Good news: none of those sessions overlap."
            return "These sessions overlap:\n" + "\n".join(f"- {c['detail']}" for c in data["conflicts"])
        if isinstance(data, dict) and "title" in data:
            return (f'{data["id"]} "{data["title"]}" is on {data["day"]} from {data["start"]} to '
                    f'{data["end"]} in {data["room"]}. Speaker: {data["speaker"]}. {data["description"]}')
        return "I am not sure. The tool result did not contain what I needed."

    # --------------------------------------------------------- multi-agent
    def _plan(self, text):
        topics = _topics(text) or ["agents"]
        return json.dumps({"day": _day(text) or "Thursday", "topics": topics[:4]})

    def _critique(self, text):
        report = re.search(r"CONFLICT REPORT:\s*(\{.*\})", text, re.S)
        data = json.loads(report.group(1)) if report else {"conflicts": []}
        if not data.get("conflicts"):
            return json.dumps({"approved": True, "issues": [], "remove": []})
        order = re.search(r"INTEREST ORDER:\s*(\[.*?\])", text, re.S)
        draft = re.search(r"DRAFT:\s*(\[.*?\])\s*(?:\n|$)", text, re.S)
        order = json.loads(order.group(1)) if order else []
        topic_of = {s["id"]: s.get("topic", "") for s in (json.loads(draft.group(1)) if draft else [])}
        rank = lambda sid: order.index(topic_of[sid]) if topic_of.get(sid) in order else len(order)
        remove = []
        for c in data["conflicts"]:
            if c["a"] in remove or c["b"] in remove:
                continue
            remove.append(c["b"] if rank(c["b"]) >= rank(c["a"]) else c["a"])
        return json.dumps({"approved": False,
                           "issues": [c["detail"] for c in data["conflicts"]],
                           "remove": remove})

    def _write(self, text):
        m = re.search(r"AGENDA:\s*(\[.*\])", text, re.S)
        agenda = json.loads(m.group(1)) if m else []
        if not agenda:
            return "Your day is wide open! I could not find sessions that match your interests."
        lines = [f'{s["start"]}  {s["title"]}  ({s["room"]})' for s in agenda]
        return ("Here is your personal iGET plan:\n\n" + "\n".join(lines) +
                "\n\nTip: rooms can fill up, so arrive a few minutes early. Enjoy the conference!")
