"""Local A/B listening-test website for the WAV renders in renders/.

Development tool only: not part of Delay Lama Everything, never packaged.
Python 3.11 standard library only; the pages are plain HTML/CSS/JS.

    py tools\\listening\\serve.py            # http://127.0.0.1:8740/
    py tools\\listening\\serve.py --port 8741 --renders <folder>

The server binds to 127.0.0.1 only. It serves the pages in static/, the WAV
files under the renders folder, and a small JSON API. Answers are saved next
to the renders as answers.json (the data) and answers.md (a readable summary).
The manifest and answer formats are described in README.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import parse_qs, unquote, urlparse

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
DEFAULT_RENDERS = HERE.parent.parent / "renders"
DEFAULT_PORT = 8740

MANIFEST = "listening.json"
ANSWERS_JSON = "answers.json"
ANSWERS_MD = "answers.md"
FORMAT = 1                      # manifest and answers format version
FALLBACK_SKIP = {"all.wav"}     # concatenations of the other clips
CONFIDENCE = ("low", "medium", "high")
MAX_BODY = 1 << 20
MAX_NOTE = 20000

SAVE_LOCK = threading.Lock()

STATIC_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
}


class ManifestError(Exception):
    pass


# --------------------------------------------------------------------------
# Discovery and manifests


def rel_posix(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    return "" if rel == "." else rel


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def text(value, field: str, default: str = "") -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise ManifestError(f"{field} must be a string")
    return value


def number(value, field: str):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ManifestError(f"{field} must be a number of seconds >= 0")
    return float(value)


def normalize_test(raw: dict, folder: Path, renders: Path, index: int) -> dict:
    """Checks one test from a manifest and fills in the defaults."""
    if not isinstance(raw, dict):
        raise ManifestError(f"tests[{index}] must be an object")
    tid = text(raw.get("id"), f"tests[{index}].id")
    if not tid:
        raise ManifestError(f"tests[{index}] needs an id")
    where = f"test {tid}"
    clips_raw = raw.get("clips")
    if not isinstance(clips_raw, list) or not clips_raw:
        raise ManifestError(f"{where}: clips must be a non-empty list")

    clips, clip_ids = [], set()
    conditions: dict[str, dict] = {}   # id -> {label, reference}
    for i, c in enumerate(clips_raw):
        if not isinstance(c, dict):
            raise ManifestError(f"{where}: clips[{i}] must be an object")
        file = text(c.get("file"), f"{where}: clips[{i}].file")
        if not file:
            raise ManifestError(f"{where}: clips[{i}] needs a file")
        path = (folder / PurePosixPath(file)).resolve()
        if not inside(path, renders):
            raise ManifestError(f"{where}: {file} is outside the renders folder")
        start = number(c.get("start"), f"{where}: clips[{i}].start")
        end = number(c.get("end"), f"{where}: clips[{i}].end")
        if start is not None and end is not None and end <= start:
            raise ManifestError(f"{where}: clips[{i}] ends before it starts")
        stem = PurePosixPath(file).stem
        cid = text(c.get("id"), f"{where}: clips[{i}].id") or stem
        if cid in clip_ids:
            cid = f"{cid}@{start or 0:g}"
        if cid in clip_ids:
            raise ManifestError(f"{where}: two clips have the id {cid}")
        clip_ids.add(cid)
        label = text(c.get("label"), f"{where}: clips[{i}].label") or stem
        cond = text(c.get("condition"), f"{where}: clips[{i}].condition") or cid
        reference = bool(c.get("reference", False))
        if cond in conditions:
            if conditions[cond]["reference"] != reference:
                raise ManifestError(f"{where}: condition {cond} is a reference in some clips only")
        else:
            conditions[cond] = {"id": cond, "label": label, "reference": reference}
        clips.append({
            "id": cid,
            "file": rel_posix(path, renders.resolve()),
            "label": label,
            "desc": text(c.get("desc"), f"{where}: clips[{i}].desc"),
            "group": text(c.get("group"), f"{where}: clips[{i}].group"),
            "condition": cond,
            "reference": reference,
            "start": start,
            "end": end,
            "missing": not path.is_file(),
        })

    question = text(raw.get("question"), f"{where}: question")
    questions_raw = raw.get("questions")
    if questions_raw is None:
        # Default: one "which is best?" question over the non-reference conditions.
        questions_raw = [{
            "id": "best",
            "text": question or "Which is best?",
            "choices": [{"id": c["id"], "label": c["label"], "condition": c["id"]}
                        for c in conditions.values() if not c["reference"]]
                       + [{"id": "none", "label": "None of them / can't tell"}],
        }]
    if not isinstance(questions_raw, list) or not questions_raw:
        raise ManifestError(f"{where}: questions must be a non-empty list")

    questions, qids = [], set()
    for qi, q in enumerate(questions_raw):
        if not isinstance(q, dict):
            raise ManifestError(f"{where}: questions[{qi}] must be an object")
        qid = text(q.get("id"), f"{where}: questions[{qi}].id") or f"q{qi + 1}"
        if qid in qids:
            raise ManifestError(f"{where}: two questions have the id {qid}")
        qids.add(qid)
        choices_raw = q.get("choices")
        if not isinstance(choices_raw, list) or len(choices_raw) < 2:
            raise ManifestError(f"{where}: question {qid} needs at least two choices")
        choices, cids = [], set()
        for ci, ch in enumerate(choices_raw):
            if not isinstance(ch, dict):
                raise ManifestError(f"{where}: question {qid} choices[{ci}] must be an object")
            chid = text(ch.get("id"), f"{where}: question {qid} choices[{ci}].id")
            if not chid or chid in cids:
                raise ManifestError(f"{where}: question {qid} has a missing or repeated choice id")
            cids.add(chid)
            cond = text(ch.get("condition"), f"{where}: question {qid} choice {chid} condition")
            if cond and cond not in conditions:
                raise ManifestError(f"{where}: question {qid} choice {chid}: no clip has condition {cond}")
            choices.append({"id": chid, "label": text(ch.get("label"), "label") or chid,
                            "condition": cond or None})
        questions.append({
            "id": qid,
            "text": text(q.get("text"), f"{where}: question {qid} text") or question or qid,
            "multi": bool(q.get("multi", False)),
            "choices": choices,
        })

    return {
        "id": tid,
        "title": text(raw.get("title"), f"{where}: title") or tid,
        "question": question,
        "notes": text(raw.get("notes"), f"{where}: notes"),
        "blind": bool(raw.get("blind", True)),
        "clips": clips,
        "conditions": list(conditions.values()),
        "questions": questions,
    }


def manifest_set(folder: Path, renders: Path) -> dict:
    rel = rel_posix(folder, renders)
    base = {"path": rel, "phase": rel.split("/")[0] if rel else "(top)",
            "source": "manifest", "title": rel or "renders", "intro": "",
            "tests": [], "error": None}
    try:
        try:
            data = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise ManifestError(f"can't read {MANIFEST}: {e}") from e
        if not isinstance(data, dict):
            raise ManifestError("the manifest must be a JSON object")
        if data.get("format", FORMAT) != FORMAT:
            raise ManifestError(f"unknown format {data.get('format')!r} (this tool reads {FORMAT})")
        base["title"] = text(data.get("title"), "title") or base["title"]
        base["intro"] = text(data.get("intro"), "intro")
        tests_raw = data.get("tests")
        if not isinstance(tests_raw, list) or not tests_raw:
            raise ManifestError("tests must be a non-empty list")
        tests, tids = [], set()
        for i, t in enumerate(tests_raw):
            nt = normalize_test(t, folder, renders, i)
            if nt["id"] in tids:
                raise ManifestError(f"two tests have the id {nt['id']}")
            tids.add(nt["id"])
            tests.append(nt)
        base["tests"] = tests
    except ManifestError as e:
        base["error"] = str(e)
    return base


def fallback_set(folder: Path, renders: Path, wavs: list[str]) -> dict:
    rel = rel_posix(folder, renders)
    name = folder.name if rel else "renders"
    raw = {
        "id": name,
        "title": name,
        "question": "Which is best?",
        "clips": [{"file": w} for w in wavs],
    }
    return {"path": rel, "phase": rel.split("/")[0] if rel else "(top)",
            "source": "fallback", "title": rel or "renders",
            "intro": f"No {MANIFEST} in this folder, so every WAV is listed "
                     "with a generic question.",
            "tests": [normalize_test(raw, folder, renders, 0)], "error": None}


def discover(renders: Path) -> list[dict]:
    """Every folder with a manifest, plus folders of WAVs no manifest uses."""
    renders = renders.resolve()
    manifest_dirs, wav_dirs = [], {}
    for dirpath, dirnames, filenames in os.walk(renders):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        d = Path(dirpath)
        if MANIFEST in filenames:
            manifest_dirs.append(d)
        wavs = sorted(f for f in filenames
                      if f.lower().endswith(".wav") and f.lower() not in FALLBACK_SKIP)
        if wavs:
            wav_dirs[d] = wavs
    sets, used = [], set()
    for d in manifest_dirs:
        s = manifest_set(d, renders)
        sets.append(s)
        for t in s["tests"]:
            for c in t["clips"]:
                used.add((renders / c["file"]).resolve())
    for d, wavs in wav_dirs.items():
        if d in manifest_dirs or any((d / w).resolve() in used for w in wavs):
            continue
        sets.append(fallback_set(d, renders, wavs))
    sets.sort(key=lambda s: s["path"])
    return sets


def find_set(renders: Path, path: str) -> dict | None:
    for s in discover(renders):
        if s["path"] == path:
            return s
    return None


# --------------------------------------------------------------------------
# Answers


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def short_time(iso: str) -> str:
    try:
        return dt.datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError):
        return str(iso)


def load_answers(folder: Path) -> dict:
    path = folder / ANSWERS_JSON
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("tests"), dict):
            return data
    except FileNotFoundError:
        pass
    except (OSError, json.JSONDecodeError) as e:
        print(f"warning: can't read {path}: {e}", file=sys.stderr)
    return {"format": FORMAT, "tests": {}}


def write_atomic(path: Path, content: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def build_entry(test: dict, body: dict) -> dict:
    """Validates a posted answer against the manifest and returns the entry to store."""
    status = body.get("status")
    if status not in ("answered", "skipped"):
        raise ValueError("status must be 'answered' or 'skipped'")
    blind = bool(body.get("blind", False))
    conds = {c["id"]: c for c in test["conditions"]}

    letters = {}
    if blind:
        raw = body.get("letters") or {}
        if not isinstance(raw, dict):
            raise ValueError("letters must be an object")
        for letter, cond in raw.items():
            if not (isinstance(letter, str) and len(letter) == 1 and letter.isupper()):
                raise ValueError(f"bad blind letter {letter!r}")
            if cond not in conds or conds[cond]["reference"]:
                raise ValueError(f"bad blind condition {cond!r}")
            letters[letter] = cond
    letter_of = {cond: letter for letter, cond in letters.items()}

    given = body.get("answers") or {}
    if not isinstance(given, dict):
        raise ValueError("answers must be an object")
    answers = []
    for q in test["questions"]:
        value = given.get(q["id"]) if status == "answered" else None
        by_id = {c["id"]: c for c in q["choices"]}
        picked = value if isinstance(value, list) else ([] if value in (None, "") else [value])
        if not q["multi"] and len(picked) > 1:
            raise ValueError(f"question {q['id']} takes one choice")
        for p in picked:
            if p not in by_id:
                raise ValueError(f"question {q['id']} has no choice {p!r}")
        picked = [c["id"] for c in q["choices"] if c["id"] in picked]  # manifest order
        item = {"question": q["id"], "text": q["text"]}
        if q["multi"]:
            item["choice"] = picked
            item["label"] = [by_id[p]["label"] for p in picked]
        else:
            item["choice"] = picked[0] if picked else None
            item["label"] = by_id[picked[0]]["label"] if picked else None
        if blind:
            lets = [letter_of.get(by_id[p]["condition"]) for p in picked]
            item["letter"] = lets if q["multi"] else (lets[0] if lets else None)
        answers.append(item)

    confidence = body.get("confidence") or None
    if confidence is not None and confidence not in CONFIDENCE:
        raise ValueError(f"confidence must be one of {', '.join(CONFIDENCE)}")
    note = body.get("note") or ""
    if not isinstance(note, str) or len(note) > MAX_NOTE:
        raise ValueError("note must be a string (at most 20000 characters)")

    entry = {"saved": now_iso(), "status": status, "blind": blind}
    if blind:
        entry["letters"] = dict(sorted(letters.items()))
    entry.update({"answers": answers, "confidence": confidence, "note": note.strip()})
    return entry


def answer_text(item: dict, with_letters: bool = True) -> str:
    label = item.get("label")
    if isinstance(label, list):
        if not label:
            return "(none ticked)"
        parts = list(label)
        if with_letters and item.get("letter"):
            parts = [f"{lab} [{let}]" if let else lab
                     for lab, let in zip(label, item["letter"])]
        return ", ".join(parts)
    if label is None:
        return "(not answered)"
    if with_letters and item.get("letter"):
        return f"{label} [picked blind as {item['letter']}]"
    return label


def entry_summary(entry: dict) -> str:
    """One line, for the index page."""
    if entry.get("status") == "skipped":
        return "skipped"
    parts = [answer_text(a, with_letters=False) for a in entry.get("answers", [])]
    tags = ["blind" if entry.get("blind") else "sighted"]
    if entry.get("confidence"):
        tags.append(entry["confidence"])
    return " · ".join(parts) + f" ({', '.join(tags)})"


def render_md(s: dict, answers: dict) -> str:
    folder = f"renders/{s['path']}" if s["path"] else "renders"
    out = [f"# Listening answers: {s['title']}", "",
           f"Folder `{folder}`. Written by `tools/listening/serve.py` on every save, "
           f"from `{ANSWERS_JSON}` (the data; this file is regenerated, so edits here are lost). "
           "Blind answers name the condition the listener picked; the letter it had is in brackets.",
           "", f"Updated {short_time(now_iso())}.", ""]
    tests = answers.get("tests", {})
    known = set()
    counts = {"answered": 0, "skipped": 0, "open": 0}
    for t in s["tests"]:
        known.add(t["id"])
        entries = tests.get(t["id"]) or []
        counts[entries[-1]["status"] if entries else "open"] += 1
    out += [f"Answered {counts['answered']}, skipped {counts['skipped']}, "
            f"not answered {counts['open']} (of {len(s['tests'])}).", ""]

    def section(tid: str, title: str, question: str, entries: list) -> None:
        nonlocal out
        out.append(f"## {tid}: {title}" if title != tid else f"## {tid}")
        out.append("")
        if question:
            out += [question, ""]
        if not entries:
            out += ["_Not answered yet._", ""]
            return
        last = entries[-1]
        mode = "blind" if last.get("blind") else "sighted"
        if last.get("status") == "skipped":
            out.append(f"**Skipped** ({short_time(last.get('saved'))}, {mode}).")
        else:
            conf = f", confidence {last['confidence']}" if last.get("confidence") else ""
            out.append(f"Latest ({short_time(last.get('saved'))}, {mode}{conf}):")
            out.append("")
            for a in last.get("answers", []):
                out.append(f"- {a.get('text')} **{answer_text(a)}**")
        if last.get("note"):
            out += ["", "Note: " + last["note"].replace("\n", "\n  ")]
        out.append("")
        if len(entries) > 1:
            out.append("Earlier answers (oldest first):")
            out.append("")
            for e in entries[:-1]:
                out.append(f"- {short_time(e.get('saved'))}: {entry_summary(e)}"
                           + (f". Note: {e['note']}" if e.get("note") else ""))
            out.append("")

    for t in s["tests"]:
        section(t["id"], t["title"], t["question"], tests.get(t["id"]) or [])
    orphans = [tid for tid in tests if tid not in known]
    if orphans:
        out += ["## Answers for tests no longer in the manifest", ""]
        for tid in orphans:
            section(tid, tid, "", tests[tid])
    return "\n".join(out).rstrip() + "\n"


def save_answer(renders: Path, body: dict) -> dict:
    path = body.get("set")
    tid = body.get("test")
    if not isinstance(path, str) or not isinstance(tid, str):
        raise ValueError("set and test are required")
    s = find_set(renders, path)
    if s is None or s["error"]:
        raise ValueError(f"no usable test set {path!r}")
    test = next((t for t in s["tests"] if t["id"] == tid), None)
    if test is None:
        raise ValueError(f"no test {tid!r} in {path!r}")
    entry = build_entry(test, body)
    folder = renders / PurePosixPath(path) if path else renders
    with SAVE_LOCK:
        data = load_answers(folder)
        data["format"] = FORMAT
        data["set"] = f"renders/{path}" if path else "renders"
        data["manifest"] = MANIFEST if s["source"] == "manifest" else None
        data["updated"] = entry["saved"]
        data["tests"].setdefault(tid, []).append(entry)
        as_json = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        as_md = render_md(s, data)          # build both before writing either
        write_atomic(folder / ANSWERS_JSON, as_json)
        write_atomic(folder / ANSWERS_MD, as_md)
    where = (folder / ANSWERS_JSON).relative_to(renders.parent) if inside(folder, renders.parent) \
        else folder / ANSWERS_JSON
    print(f"saved {tid} ({entry['status']}) -> {where}", flush=True)
    return {"ok": True, "entries": data["tests"][tid]}


# --------------------------------------------------------------------------
# HTTP


class Handler(BaseHTTPRequestHandler):
    server_version = "ListeningTests/1"
    renders: Path = DEFAULT_RENDERS
    port: int = DEFAULT_PORT

    def log_message(self, fmt, *args):  # quiet: only errors are printed
        pass

    def log_error(self, fmt, *args):
        sys.stderr.write("error: " + (fmt % args) + "\n")

    # -- helpers

    def send_bytes(self, status: int, data: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def send_json(self, obj, status: int = 200) -> None:
        self.send_bytes(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                        "application/json; charset=utf-8")

    def fail(self, status: int, message: str) -> None:
        self.send_json({"ok": False, "error": message}, status)

    def send_file(self, path: Path, ctype: str) -> None:
        try:
            data = path.read_bytes()
        except OSError:
            self.fail(404, "not found")
            return
        self.send_bytes(200, data, ctype)

    def host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").lower()
        return host in (f"127.0.0.1:{self.port}", f"localhost:{self.port}")

    # -- routes

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self.host_ok():
            return self.fail(403, "use http://127.0.0.1:%d/" % self.port)
        url = urlparse(self.path)
        route = unquote(url.path)
        query = parse_qs(url.query)
        if route in ("/", "/index.html"):
            return self.send_file(STATIC / "index.html", STATIC_TYPES[".html"])
        if route in ("/test", "/test.html"):
            return self.send_file(STATIC / "test.html", STATIC_TYPES[".html"])
        if route.startswith("/static/"):
            name = route[len("/static/"):]
            path = (STATIC / name).resolve()
            ctype = STATIC_TYPES.get(path.suffix.lower())
            if ctype and inside(path, STATIC) and path.is_file():
                return self.send_file(path, ctype)
            return self.fail(404, "not found")
        if route.startswith("/renders/"):
            path = (self.renders / route[len("/renders/"):]).resolve()
            if path.suffix.lower() == ".wav" and inside(path, self.renders) and path.is_file():
                return self.send_file(path, "audio/wav")
            return self.fail(404, "not found")
        if route == "/api/sets":
            return self.send_json({"ok": True, "renders": str(self.renders),
                                   "sets": self.set_summaries()})
        if route == "/api/set":
            path = (query.get("path") or [""])[0]
            s = find_set(self.renders, path)
            if s is None:
                return self.fail(404, f"no test set {path!r}")
            folder = self.renders / PurePosixPath(path) if path else self.renders
            answers = load_answers(folder).get("tests", {})
            return self.send_json({"ok": True, "set": s, "answers": answers,
                                   "answers_md": f"renders/{path}/{ANSWERS_MD}".replace("//", "/")})
        if route == "/favicon.ico":
            return self.send_bytes(204, b"", "image/x-icon")
        return self.fail(404, "not found")

    def do_POST(self):
        if not self.host_ok():
            return self.fail(403, "use http://127.0.0.1:%d/" % self.port)
        origin = self.headers.get("Origin")
        if origin and origin.lower() not in (f"http://127.0.0.1:{self.port}",
                                             f"http://localhost:{self.port}"):
            return self.fail(403, "cross-origin requests are not accepted")
        if urlparse(self.path).path != "/api/answer":
            return self.fail(404, "not found")
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self.fail(415, "send JSON")
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length <= 0 or length > MAX_BODY:
            return self.fail(400, "bad request size")
        try:
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(body, dict):
                raise ValueError("send a JSON object")
            result = save_answer(self.renders, body)
        except (ValueError, UnicodeDecodeError) as e:
            return self.fail(400, str(e))
        except OSError as e:
            return self.fail(500, f"can't write the answers: {e}")
        except Exception as e:  # report, don't drop the connection
            self.log_error("saving failed: %r", e)
            return self.fail(500, f"server error: {e!r}")
        return self.send_json(result)

    def set_summaries(self) -> list[dict]:
        out = []
        for s in discover(self.renders):
            folder = self.renders / PurePosixPath(s["path"]) if s["path"] else self.renders
            answers = load_answers(folder).get("tests", {})
            tests = []
            for t in s["tests"]:
                entries = answers.get(t["id"]) or []
                last = entries[-1] if entries else None
                tests.append({
                    "id": t["id"], "title": t["title"], "question": t["question"],
                    "clips": len(t["clips"]),
                    "missing": sum(1 for c in t["clips"] if c["missing"]),
                    "status": last["status"] if last else None,
                    "saved": last["saved"] if last else None,
                    "times": len(entries),
                    "summary": entry_summary(last) if last else "",
                })
            out.append({k: s[k] for k in ("path", "phase", "source", "title", "intro", "error")}
                       | {"tests": tests,
                          "has_answers": (folder / ANSWERS_MD).is_file()})
        return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Local A/B listening tests for renders/.")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port (default {DEFAULT_PORT})")
    ap.add_argument("--renders", type=Path, default=DEFAULT_RENDERS,
                    help="folder of renders (default: the repo's renders/)")
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    args = ap.parse_args()

    renders = args.renders.resolve()
    if not renders.is_dir():
        print(f"no renders folder at {renders}", file=sys.stderr)
        return 1
    Handler.renders = renders
    Handler.port = args.port
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError as e:
        print(f"can't listen on 127.0.0.1:{args.port} ({e}).\n"
              f"Is the server already running? Then open http://127.0.0.1:{args.port}/ "
              "or pass --port.", file=sys.stderr)
        return 1
    httpd.daemon_threads = True
    url = f"http://127.0.0.1:{args.port}/"
    sets = discover(renders)
    print(f"Listening tests: {url}")
    print(f"Renders: {renders} ({len(sets)} test sets). Ctrl+C stops the server.", flush=True)
    for s in sets:
        if s["error"]:
            print(f"  manifest problem in {s['path']}: {s['error']}", file=sys.stderr)
    if args.open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
