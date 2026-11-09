"""Phase 4b ear check: the articulator in DelayLamaVoice.exe (protocol 1).

Run: py renders/phase4b/make_4b.py [<DelayLamaVoice.exe>]

Renders the phase 4a A/B lines (renders/phase4a/ab/make_ab.py, imported read
only) through the real articulator with the profiles in
profiles/imitation.json, and writes WAVs, the scripts (scripts/) and
listening.json for tools/listening.

1. onsets/: the four onset glitches (bass and flute "laser", trumpet high
   pitch, guitar "too high between hits"), as heard in phase 4a and with the
   articulator: onset.mask 0 (no masking), 2 (the default) and a steady onset
   vowel. Gervill as the reference.
2. demos/: other profiles on the same band piece.
"""

import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path[:0] = [str(HERE / "diag"), str(ROOT / "tools" / "profiles"), str(ROOT / "renders" / "phase4a" / "ab")]
sys.dont_write_bytecode = True  # nothing written into renders/phase4a
import dl  # noqa: E402
import expand  # noqa: E402
import make_ab  # noqa: E402

AB = ROOT / "renders" / "phase4a" / "ab"
FIX = ROOT / "renders" / "phase1-fix"
EXE = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else dl.EXE
DATA = expand.load()


def script(notes, profile, extra=(), cc7=100):
    """notes: (start ms, note or chord tuple, length ms). Durations go in `on`
    (protocol 1); the written pitch, since the helper adds the octave (D14)."""
    events = []
    for start, note, length in notes:
        for n in (note if isinstance(note, tuple) else (note,)):
            events.append((start + length, 0, f"off {n}"))
            events.append((start, 1, f"on {n} 100 {length:g}"))
    events.sort(key=lambda e: (e[0], e[1]))
    lines = ["hello 1", "set articulator 1", f"cc 7 {cc7}"]
    lines += expand.set_lines(expand.resolve(DATA, profile))
    lines += [f"set {k} {v:g}" for k, v in extra]
    t = 0.0
    for when, _, text in events:
        if when > t:
            lines.append(f"wait {when - t:g}")
            t = when
        lines.append(text)
    return "\n".join(lines) + "\n"


def render(name, text, monks=1):
    path = HERE / "scripts" / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return dl.render(path, exe=EXE, monks=monks, tail=1200)


def clip_set(test_id, title, question, notes, clips, questions, group_gain=True):
    folder = HERE / test_id
    folder.mkdir(exist_ok=True)
    n = max(len(x) for *_, x in clips)
    peak = max(np.abs(x).max() for *_, x in clips)
    entries = []
    for k, (file, label, desc, condition, reference, x) in enumerate(clips, 1):
        scale = 0.89 / (peak if group_gain else np.abs(x).max())
        y = np.vstack([x, np.zeros((n - len(x), 2))]) * scale
        name = f"{test_id}/{k:02d}_{file}.wav"
        dl.write_wav(HERE / name, y)
        entry = {"file": name, "label": label, "desc": desc, "condition": condition}
        if reference:
            entry["reference"] = True
        entries.append(entry)
    return {"id": test_id.replace("/", "_"), "title": title, "question": question, "notes": notes,
            "clips": entries, "questions": questions}


def choices(conds, extra=()):
    return [{"id": c, "label": label, "condition": c} for c, label in conds] + list(extra)


def onset_test(test_id, title, glitch, ab_folder, fix_clip, notes, profile, monks=1, extra_note=""):
    gervill = dl.read_wav(AB / ab_folder / "01_gervill_solo.wav")
    before = dl.read_wav(FIX / ab_folder / fix_clip)
    variants = [("mask0", "Articulator, no mask", "onset.mask 0: the onset vowel at full level",
                 [("onset.mask", 0)]),
                ("mask2", "Articulator (default)", "onset.mask 2: the level rises over twice "
                 "the onset vowel move", []),
                ("steady", "Articulator, steady onset", "No onset vowel move at all "
                 "(onset.vowel null)", [("onset.vowel", -1)])]
    clips = [("gervill", "Gervill", "What midis2jam2 plays (reference)", "gervill", True, gervill),
             ("phase4a", "Phase 4a (heard before)", "The render from the phase 1 fix A/B "
              "('After'), made by the phase 4a prototype articulator", "phase4a", False, before)]
    for cond, label, desc, extra in variants:
        x = render(f"{test_id}_{cond}", script(notes, profile, extra), monks)
        clips.append((cond, label, desc, cond, False, x))
    conds = [("phase4a", "Phase 4a"), ("mask0", "No mask"), ("mask2", "Default"),
             ("steady", "Steady onset")]
    questions = [
        {"id": "still", "text": f"Which clips still have the {glitch}?", "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "best", "text": "Which sounds most like someone imitating the instrument?",
         "multi": False, "choices": choices(conds[1:], [{"id": "cant_tell", "label": "Can't tell"}])},
    ]
    return clip_set(f"onsets/{test_id}", title,
                    f"{title}: which clips still have the {glitch}?",
                    f"Profile '{profile}' from profiles/imitation.json, sung by the articulator "
                    "(DelayLamaVoice protocol 1). One gain for the monk clips; Gervill is the "
                    "reference." + extra_note, clips, questions)


def demo_test():
    pieces = [
        ("sax", "Tenor sax", "sax.tenor", make_ab.melody(-12), 1, "c04_sax"),
        ("violin", "Violin", "strings.violin", make_ab.melody(12), 1, "c06_violin"),
        ("piano", "Piano chords (4 monks)", "piano", make_ab.piano_chords(), 4, "c02_piano"),
        ("organ", "Drawbar organ chords (4 monks)", "organ", make_ab.piano_chords(), 4, None),
        ("choir", "Choir aahs chords (4 monks)", "choir.aahs", make_ab.piano_chords(), 4, None),
        ("clean_guitar", "Clean guitar lead", "guitar.clean", make_ab.melody(-12), 1, None),
    ]
    clips = []
    for key, label, profile, notes, monks, ab in pieces:
        x = render(f"demo_{key}", script(notes, profile), monks)
        clips.append((key, label, f"Profile '{profile}'", key, False, x))
    conds = [(c[0], c[1]) for c in clips]
    questions = [
        {"id": "works", "text": "Which ones sound like a person imitating that instrument?",
         "multi": True, "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "glitch", "text": "Which ones have a glitch (laser, whistle, click, wrong pitch)?",
         "multi": True, "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
    ]
    return clip_set("demos", "Profile demos",
                    "First-guess profiles through the articulator: do they imitate the instrument?",
                    "Each clip is normalised on its own (different instruments). Tuning is phase "
                    "4c; this checks that the articulator plays the profiles without glitches.",
                    clips, questions, group_gain=False)


def main():
    for d in ("scripts", "onsets"):
        (HERE / d).mkdir(exist_ok=True)
    tests = [
        onset_test("c01_bass", "Bass", "laser-gun start", "c01_bass", "02_after.wav",
                   make_ab.bass_line(), "bass.finger"),
        onset_test("c05_flute", "Flute", "plucked laser-gun start", "c05_flute", "02_after.wav",
                   make_ab.melody(12), "flute",
                   extra_note=" The flute profile ('h-u') has no onset vowel move, so the three "
                   "articulator clips are the same: the phase 4a flute's laser came from its 0.55 "
                   "dip vowel, which this profile drops."),
        onset_test("c03_trumpet", "Trumpet", "high pitch at the start of some notes",
                   "c03_trumpet", "02_after.wav", make_ab.melody(0), "trumpet"),
        onset_test("c07_guitar", "Overdrive guitar", "'too high between two hits'",
                   "c07_guitar", "03_after_bend_on_time.wav", make_ab.melody(-12),
                   "guitar.overdrive"),
        demo_test(),
    ]
    manifest = {
        "format": 1,
        "title": "Phase 4b: the articulator",
        "intro": "DelayLamaVoice now shapes every note itself (protocol 1, 1 ms control ticks) "
                 "from the profiles in profiles/imitation.json. The onset glitches came from "
                 "the vowel moving at full level near a note's start: Delay Lama's formants "
                 "are narrow, so a moving vowel is heard as a falling ping (low notes) or a "
                 "whistle where it crosses a harmonic (high notes). onset.mask keeps the level "
                 "low until the vowel has arrived. Whether that sounds right is your call.",
        "tests": tests,
    }
    (HERE / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("wrote", sum(len(t["clips"]) for t in tests), "clips")


if __name__ == "__main__":
    main()
