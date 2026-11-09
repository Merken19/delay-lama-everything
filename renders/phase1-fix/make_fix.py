"""Phase 1 fix: before/after renders of the onset glitches heard in the phase 4a
A/B set (renders/phase4a/ab/answers.md), for the listening site.

Run: py make_fix.py <before DelayLamaVoice.exe> [<after DelayLamaVoice.exe>]
  before: the helper as of commit 19b74e8 (phase 1), which made the phase 4a renders
  after:  default external/delalalalay-lama/Windows/build/Release/DelayLamaVoice.exe

Each test renders a phase 4a script (renders/phase4a/ab/scripts, read only)
with both helpers. Where the cause is in the script or the profile rather than
the helper, a diagnostic copy of the script (scripts/ here) changes only that
one thing, so the ear can confirm the cause. One gain per test keeps the clips'
loudness comparable. Writes the WAVs, scripts/ and listening.json.
"""

import json
import pathlib
import re
import subprocess
import sys
import wave

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = ROOT / "renders" / "phase4a" / "ab" / "scripts"
AFTER = ROOT / "external" / "delalalalay-lama" / "Windows" / "build" / "Release" / "DelayLamaVoice.exe"
SR = 48000


def read_wav(path):
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
    return x.reshape(-1, 2) / 32768


def write_wav(path, x):
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def render(exe, script, tag, monks=1):
    out = HERE / "tmp" / f"{script.stem}_{tag}.wav"
    subprocess.run([str(exe), "--render", str(script), str(out), "--monks", str(monks),
                    "--tail", "1500"], check=True, capture_output=True)
    return read_wav(out)


# --- Diagnostic script copies -------------------------------------------------------

def steady(lines, key, value):
    """Every `set <key>` holds one value: removes that curve from the script."""
    return [f"set {key} {value}" if re.match(rf"set {key} ", line) else line for line in lines]


def bend_with_note(lines, window_ms=10.0, jump=683):
    """Where a note starts unbent and its first bend, within window_ms, jumps by
    more than `jump` (683 = 1 semitone at bendrange 12), moves that bend to just
    before the note-on, so the slide starts from its first pitch instead of
    sounding the target first. Ordinary scoops are left alone."""
    out = list(lines)
    bend, i = 8192, 0
    while i < len(out):
        if out[i].startswith("bend "):
            bend = int(out[i].split()[1])
        elif out[i].startswith("on "):
            elapsed, j = 0.0, i + 1
            while j < len(out) and elapsed <= window_ms and not out[j].startswith("on "):
                if out[j].startswith("wait "):
                    elapsed += float(out[j].split()[1])
                elif out[j].startswith("bend "):
                    if elapsed > 0 and abs(int(out[j].split()[1]) - bend) > jump:
                        out.insert(i, out.pop(j))
                        i += 1
                    break
                j += 1
        i += 1
    return out


def variant(name, tag, change, note):
    lines = (SOURCE / f"{name}.txt").read_text(encoding="utf-8").splitlines()
    lines = [f"# Diagnostic copy of renders/phase4a/ab/scripts/{name}.txt: {note}"] + change(lines)
    path = HERE / "scripts" / f"{name}_{tag}.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# --- Tests --------------------------------------------------------------------------

def test(test_id, title, question, notes, clips, questions):
    """clips: [(file, label, desc, condition, signal)]."""
    folder = HERE / test_id
    folder.mkdir(exist_ok=True)
    n = max(len(x) for *_, x in clips)
    peak = max(np.abs(x).max() for *_, x in clips)
    scale = 0.89 / peak
    entries = []
    for k, (file, label, desc, condition, x) in enumerate(clips, 1):
        y = np.vstack([x, np.zeros((n - len(x), 2))]) * scale
        name = f"{test_id}/{k:02d}_{file}.wav"
        write_wav(HERE / name, y)
        entries.append({"file": name, "label": label, "desc": desc, "condition": condition})
    return {"id": test_id, "title": title, "question": question, "notes": notes,
            "clips": entries, "questions": questions}


def still_there(text, conditions):
    return {"id": "still", "text": text, "multi": True,
            "choices": [{"id": c, "label": label, "condition": c} for c, label in conditions]
            + [{"id": "none", "label": "None of them"}]}


def changed_regions(a, b):
    d = np.abs(a[:min(len(a), len(b))] - b[:min(len(a), len(b))]).max(axis=1)
    idx = np.nonzero(d > 1e-4)[0]
    return (idx[0] / SR, idx[-1] / SR) if len(idx) else None


def main():
    before = pathlib.Path(sys.argv[1])
    after = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else AFTER
    for d in ("tmp", "scripts"):
        (HERE / d).mkdir(exist_ok=True)
    tests = []

    # c01 bass: the helper fix, plus the onset vowel sweep removed.
    name = "c01_bass_+0"
    src = SOURCE / f"{name}.txt"
    x_before, x_after = render(before, src, "before"), render(after, src, "after")
    vowel = variant(name, "steady_vowel", lambda l: steady(l, "vowel", 0.12),
                    "vowel held at 0.12 (no 0.55 -> 0.12 sweep at each start)")
    x_vowel = render(after, vowel, "variant")
    # The same bass from the phase 4a generator after its two timing fixes
    # (renders/phase4a/make_palette.py, imported read only; nothing is written there).
    sys.path[:0] = [str(SOURCE.parent), str(SOURCE.parent.parent)]
    sys.dont_write_bytecode = True  # no __pycache__ in renders/phase4a
    import make_ab
    import make_palette
    take = make_palette.Take(name, name, 1)
    make_palette.header(take)
    make_palette.sing(take, make_ab.phrase(make_ab.bass_line(), "new", 0), make_ab.DUM)
    regen = HERE / "scripts" / "c01_bass_+0_fixed_generator.txt"
    regen.write_text("# c01_bass_+0 from renders/phase4a/make_palette.py after its timing fixes\n"
                     + take.script(), encoding="utf-8")
    x_regen_before, x_regen_after = render(before, regen, "before"), render(after, regen, "after")
    print("c01 before/after differ", changed_regions(x_before, x_after))
    tests.append(test(
        "c01_bass", "Bass: the 'laser gun' start",
        "Bass line as written (c01). Which clips still start notes like a laser gun?",
        "Before: the phase 4a render. After: the helper fix (a note's tail no longer jumps "
        "back to full level when the script raises the gain for the next note, 15 ms early). "
        "Steady vowel: after, plus a diagnostic script copy that holds the vowel at 0.12, "
        "removing the profile's fast 'a' to 'u' sweep at each start. Fixed generator: the "
        "script regenerated by phase 4a's generator after its two timing fixes, with the old "
        "and the fixed helper.",
        [("before", "Before", "Phase 4a render, helper before the fix", "before", x_before),
         ("after", "After", "Helper fix", "after", x_after),
         ("after_steady_vowel", "After, steady vowel", "Helper fix, and the onset vowel sweep "
          "removed from a copy of the script", "steady_vowel", x_vowel),
         ("fixed_generator_before", "Fixed generator, old helper", "Phase 4a generator after "
          "its timing fixes, helper before the fix", "regen_before", x_regen_before),
         ("fixed_generator_after", "Fixed generator, helper fix", "Phase 4a generator after "
          "its timing fixes, helper fix", "regen_after", x_regen_after)],
        [still_there("Which clips still have the laser-gun start?",
                     [("before", "Before"), ("after", "After"), ("steady_vowel", "After, steady vowel"),
                      ("regen_before", "Fixed generator, old helper"),
                      ("regen_after", "Fixed generator, helper fix")])]))

    # c05 flute: no helper change; the dip vowel 0.55 removed.
    name = "c05_flute_+0"
    src = SOURCE / f"{name}.txt"
    x_before, x_after = render(before, src, "before"), render(after, src, "after")
    vowel = variant(name, "steady_vowel", lambda l: steady(l, "vowel", 0.2),
                    "vowel held at 0.2 (no 0.55 dip vowel and sweep at each start)")
    x_vowel = render(after, vowel, "variant")
    print("c05 before/after differ", changed_regions(x_before, x_after))
    tests.append(test(
        "c05_flute", "Flute: the 'plucked laser gun'",
        "Flute line as written (c05). Which clips still sound like a plucked laser gun?",
        "Before and after are the same apart from the last note's tail (the helper fix does "
        "not reach this script). Steady vowel: a diagnostic script copy that holds the vowel "
        "at 0.2, removing the profile's 0.55 dip vowel and its sweep at each start.",
        [("before", "Before", "Phase 4a render, helper before the fix", "before", x_before),
         ("after", "After", "Helper fix", "after", x_after),
         ("after_steady_vowel", "After, steady vowel", "Helper fix, and the onset dip vowel "
          "removed from a copy of the script", "steady_vowel", x_vowel)],
        [still_there("Which clips still sound like a plucked laser gun?",
                     [("before", "Before"), ("after", "After"), ("steady_vowel", "After, steady vowel")])]))

    # c07 guitar: the slide's first bend sent with the note-on.
    name = "c07_guitar_+0"
    src = SOURCE / f"{name}.txt"
    x_before, x_after = render(before, src, "before"), render(after, src, "after")
    timed = variant(name, "bend_on_time", bend_with_note, "each slide's first bend moved to "
                    "just before its note-on (the original sends it 5 ms after)")
    x_timed = render(after, timed, "variant")
    print("c07 before/after differ", changed_regions(x_before, x_after))
    tests.append(test(
        "c07_guitar", "Guitar: too high between two hits",
        "Guitar line as written (c07). Which clips still go too high (or mix two pitches) "
        "between notes?",
        "Before and after are the same apart from the last note's tail. Bend on time: a "
        "diagnostic script copy where each slide's starting bend arrives with its note-on. "
        "In the original it arrives 5 ms later, so every slid note first sounds 5 ms at its "
        "target pitch, then drops about 3 semitones and slides back up.",
        [("before", "Before", "Phase 4a render, helper before the fix", "before", x_before),
         ("after", "After", "Helper fix", "after", x_after),
         ("after_bend_on_time", "After, bend on time", "Helper fix, and each slide's first "
          "bend sent with its note-on in a copy of the script", "bend_on_time", x_timed)],
        [still_there("Which clips still go too high between notes?",
                     [("before", "Before"), ("after", "After"), ("bend_on_time", "After, bend on time")])]))

    # c03 trumpet: the breath burst held steady.
    name = "c03_trumpet_+0"
    src = SOURCE / f"{name}.txt"
    x_before, x_after = render(before, src, "before"), render(after, src, "after")
    breath = variant(name, "steady_breath", lambda l: steady(l, "breath", 0.45),
                     "breath held at 0.45 (no breath burst at each start)")
    x_breath = render(after, breath, "variant")
    print("c03 before/after differ", changed_regions(x_before, x_after))
    tests.append(test(
        "c03_trumpet", "Trumpet: the slight super high pitch",
        "Trumpet line as written (c03). Which clips still have the slight super high pitch?",
        "Before and after are the same apart from the last note's tail. Two suspects: the "
        "profile's breath burst at the start of every note, and a whistle near 3 kHz on the "
        "A4, B4 and D5 notes, where the third formant meets a harmonic (it starts about 60 ms "
        "into those notes and holds). Steady breath removes the burst only.",
        [("before", "Before", "Phase 4a render, helper before the fix", "before", x_before),
         ("after", "After", "Helper fix", "after", x_after),
         ("after_steady_breath", "After, steady breath", "Helper fix, and the breath burst "
          "removed from a copy of the script", "steady_breath", x_breath)],
        [still_there("Which clips still have the high pitch?",
                     [("before", "Before"), ("after", "After"), ("steady_breath", "After, steady breath")]),
         {"id": "when", "text": "Where is the high pitch, in the clips that have it?", "multi": False,
          "choices": [{"id": "every_start", "label": "At the start of every note"},
                      {"id": "some_notes", "label": "Only on some notes, held through the note"},
                      {"id": "both", "label": "Both"},
                      {"id": "cant_tell", "label": "Can't tell"}]}]))

    manifest = {
        "format": 1,
        "title": "Phase 1 fix: onset glitches in DelayLamaVoice",
        "intro": "The glitches from the phase 4a listening test, before and after the helper fix "
                 "(DelayLamaVoice keeps a released note's tail from getting louder). Clips marked "
                 "'steady' or 'on time' also use a diagnostic copy of the phase 4a script with one "
                 "thing changed, to tell helper bugs from script and profile causes. Monk alone, "
                 "dry, as written; one gain per test.",
        "tests": tests,
    }
    (HERE / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for f in (HERE / "tmp").iterdir():
        f.unlink()
    (HERE / "tmp").rmdir()


if __name__ == "__main__":
    main()
