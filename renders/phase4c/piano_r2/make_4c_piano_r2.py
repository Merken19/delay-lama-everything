"""Phase 4c, piano round 2 (IMITATION.md 16, "Phase 4c: piano").

Round 1 answers (renders/phase4c/piano/answers.md, 2026-11-05):
- chords alone: "Now" and "Locked" detuned, "Locked, longer" not; it was the
  most piano-like. Every chord clip glitched ("a very slight bug with the
  first notes: at the end of the note it sounds like a high pitch").
- lines: every decay rang about right. "Longer, no ng" had the right endings,
  was the most piano-like, and it was the only clip without a glitch. So the
  glitch is the "ng" ending (measured: it lifts a harmonic 24-43 dB as the note
  ends).
- band: "Now, 4 monks" was best. Both candidates (locked and longer, with "ng",
  4 or 6 monks) sounded detuned there, the same part that was in tune alone.

Two causes could explain the band result. The lock makes the whole chord wobble
as one (+-0.2 st) against Gervill's steady bass, and the longer decay leaves
each chord ringing into the next bass note. So round 2 crosses the two, with
"ng" off in all four, in the band; a short chords test checks that dropping
"ng" removes the high pitch at the note ends.

Run: py renders/phase4c/piano_r2/make_4c_piano_r2.py
"""

import json
import pathlib
import shutil
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROUND1 = HERE.parent / "piano"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROUND1))
import make_4c_piano as r1  # noqa: E402
from make_4c_piano import pp  # noqa: E402

# Round 1's helpers write into their module's folders; point them here.
r1.HERE = HERE
r1.TMP = HERE / "tmp"
r1.SCRIPTS = HERE / "scripts"
r1.gervill = lambda name: pp.gervill(ROUND1 / "midi" / f"{name}.mid", r1.TMP / f"{name}.wav")

LOCK, LONG, OPEN = r1.LOCK, r1.LONG, r1.OPEN


def chords(report):
    return r1.solo_test(
        report, "chords", "Piano chords: the high pitch at the note ends",
        "Piano part alone, 4 monks: which have the high pitch when a note ends?",
        "Round 1's winner, 'Locked, longer', against the same without the 'ng' ending (the "
        "only clip in round 1 you heard without a glitch had no 'ng'). Every clip at Gervill's "
        "loudness.",
        "piano_part", pp.piano_part(),
        [("locked_long", "Locked, longer (round 1)", "Round 1's winner, ending on 'ng'",
          LOCK + LONG),
         ("locked_long_open", "Locked, longer, no ng", "The same, the vowel held as it fades",
          LOCK + LONG + OPEN)],
        [{"id": "detuned", "text": r1.DETUNED, "multi": True,
          "choices": [{"id": "none", "label": "None of them"}]}])


def band(report):
    full = r1.gervill("band")
    rest = r1.gervill("band_no_piano")
    piano = r1.gervill("piano_part")
    target = r1.lufs(full)
    report += ["## band/", "",
               f"Gervill: the full band {target:.1f} LUFS, its piano alone {r1.lufs(piano):.1f} "
               f"LUFS, the band without piano {r1.lufs(rest):.1f} LUFS. Live mix as in round 1: "
               f"the band without piano {r1.BALANCE_DB:g} dB down (D36) plus the helper at its "
               "own level, then the whole mix at the full band's loudness. 4 monks.", "",
               "| Clip | Monks alone (LUFS) | Monks vs Gervill's piano (dB) | Live mix peak before matching | Mix gain |",
               "| --- | --- | --- | --- | --- |"]
    variants = [
        ("now", "Now (round 1's pick)", "The piano profile as it is, with 'ng'", []),
        ("open", "Short, own wobble", "No 'ng'; each monk wobbles on its own", OPEN),
        ("open_lock", "Short, locked", "No 'ng'; the monks of a chord wobble together",
         OPEN + LOCK),
        ("open_long", "Long, own wobble", "No 'ng'; rings as long as Gervill's piano",
         OPEN + LONG),
        ("open_lock_long", "Long, locked", "No 'ng'; rings longer and wobbles together",
         OPEN + LOCK + LONG),
    ]
    clips = [("gervill", "Gervill only", "What midis2jam2 plays without Delay Lama", True, full)]
    for cond, label, desc, extra in variants:
        monk = r1.render(f"band_{cond}", pp.piano_part(), extra, 4)
        n = max(len(rest), len(monk))
        mix = r1.pad(rest, n) * 10 ** (-r1.BALANCE_DB / 20) + r1.pad(monk, n)
        y = r1.match(mix, target)
        report.append(f"| {cond} | {r1.lufs(monk):.1f} | {r1.lufs(monk) - r1.lufs(piano):+.1f} | "
                      f"{20 * np.log10(np.abs(mix).max()):.1f} dBFS | "
                      f"{target - r1.lufs(mix):+.1f} dB |")
        clips.append((cond, label, desc, False, y))
    report.append("")
    conds = [(c[0], c[1]) for c in clips if not c[3]]
    none = [{"id": "none", "label": "None of them"}]
    questions = [
        {"id": "best", "text": "Which works best as the piano in the band?", "multi": False,
         "choices": r1.choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
        {"id": "detuned", "text": r1.DETUNED, "multi": True, "choices": r1.choices(conds, none)},
        {"id": "muddy", "text": "Which sound muddy or smeared (chords ringing into each other)?",
         "multi": True, "choices": r1.choices(conds, none)},
        {"id": "glitch", "text": r1.GLITCH, "multi": True, "choices": r1.choices(conds, none)},
    ]
    return r1.clip_set(
        "band", "Piano in the band: the lock or the long decay?",
        "Drums and bass from Gervill, the piano part sung: which works best, and which sound "
        "detuned?",
        "In round 1 the locked, longer piano sounded detuned in the band but not alone. Two "
        "possible causes, crossed here: the lock (the whole chord wobbles as one against "
        "Gervill's steady bass) and the long decay (each chord rings into the next bass note). "
        "All four new clips drop the 'ng' ending. Mixed as live playback plays it, every mix at "
        "the same loudness; blind mode is worth it.",
        clips, questions)


def main():
    for d in (r1.TMP, r1.SCRIPTS):
        d.mkdir(exist_ok=True)
    report = ["# Phase 4c piano round 2: levels", "",
              "Written by `make_4c_piano_r2.py`. Loudness by ITU-R BS.1770 (gated, LUFS).", ""]
    tests = [band(report), chords(report)]
    manifest = {
        "format": 1,
        "title": "Phase 4c piano, round 2: the band",
        "intro": "Round 1: no 'ng' ending (it made the high pitch at the note ends) and the "
                 "longer decay won alone, but the locked, longer piano sounded detuned in the "
                 "band. This round finds which of the two changes does that, with 'ng' off "
                 "throughout, and checks the note ends of the chords without 'ng'.",
        "tests": tests,
    }
    (HERE / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (HERE / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    shutil.rmtree(r1.TMP)
    print("\n".join(report))
    print("wrote", sum(len(t["clips"]) for t in tests), "clips")


if __name__ == "__main__":
    main()
