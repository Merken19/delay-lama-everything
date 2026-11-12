"""Tuning set for the pipe family (GM programs 73-80, profile `flute`; see
IMITATION.md sections 15-16; c05's "not like a flute at all, more like a plucked laser
gun"). The 4a clip's laser was its dip vowel, which the articulator's profile
no longer has; this is the first time the articulator's flute is heard.

What the measurements found (measure_4c_pipe.py, measure/measurements.md, and
the formant sweep in this script's report):
- The monk's flute is buzzy: from sung C5 up, nearly all its energy is above
  1.5 kHz (Gervill's flute: 6-15 dB below its total), because the DSP's third
  formant (2.2-2.9 kHz, the same level as the other two) and the breath
  partials (3.8, 4.95 kHz) lift whichever harmonic meets them; at A5 the 3rd
  harmonic is 7 dB over the fundamental, a whistle above the note.
- New helper keys voice.formant1-3 (DSP addition monk_synth_set_formant_scale:
  each formant's frequencies times a factor, 0 = silent, 1 = today's sound
  exactly). With F3 off the flute's high share is Gervill's (-6 to -15 dB) from
  sung E4 to C6, and less breath darkens it further.
- The octave fold moves flute parts by octaves (melody.mid, median B5, sings an octave
  down). Above written C6 the fundamental stays weak even without F3, so the
  fold stays.
- Onsets: the largest rises in a note's first 80 ms are all on slurred notes
  (bins between the harmonics, 20-80 ms, at the re-articulated jump or along
  a legato glide); tongued notes show none.
- Level: the profile's monk is ~6 dB under Gervill's flute (melody.mid), and
  F3 off takes another 4-5 dB off; the new profile key dyn.gain makes that up
  (the band candidates get the gain that matches 'now').

Two tests:
1. melody/: eight bars mixing slurred pairs and tongued notes, alone: now,
   F3 off, F3 off with less breath (0.3), F3 off with slurs sung legato
   (auto phrasing, quick glide), and both. Every clip at Gervill's loudness.
2. band/: the melody with Gervill's string pad, bass and drums, mixed as live
   playback plays it (Gervill 6 dB down, the live balance; the monk at its own level,
   which the report gives): now, and the two legato F3-off candidates.

Run: py tools/tuning/pipe/make_4c_pipe.py  (writes renders/tuning/pipe/)
"""

import json
import pathlib
import shutil
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import pipe_phrases as fp  # noqa: E402
from pipe_phrases import dl, pp  # noqa: E402

WORK = fp.WORK  # renders/tuning/<family>/, where the output goes

sys.path.insert(0, str(HERE.parent / "piano"))
from make_4c_piano import lufs, active_rms_db, match, pad, choices  # noqa: E402

TMP = WORK / "tmp"
SCRIPTS = WORK / "scripts"
BALANCE_DB = 6.0

NO_F3 = [("voice.formant3", 0)]
DARK = [("body.breath", 0.3)]
LEGATO = [("phrase.mode", 0), ("phrase.glide", 0.1)]

GLITCH = "Which clips have a glitch (laser, pew, whistle above the note, click, wobble)?"
BEST = "Which sounds most like someone imitating a flute?"


def render(name, phrase, extra=()):
    text = fp.script(phrase, fp.profile(), extra)
    path = SCRIPTS / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return dl.render(path, monks=1, tail=800)


def gervill(name):
    return pp.gervill(WORK / "midi" / f"{name}.mid", TMP / f"{name}.wav")


def clip_set(test_id, title, question, notes, clips, questions):
    folder = WORK / test_id
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir()
    n = max(len(x) for *_, x in clips)
    scale = 0.89 / max(np.abs(x).max() for *_, x in clips)
    entries = []
    for k, (cond, label, desc, reference, x) in enumerate(clips, 1):
        name = f"{test_id}/{k:02d}_{cond}.wav"
        dl.write_wav(WORK / name, pad(x, n) * scale)
        entry = {"file": name, "label": label, "desc": desc, "condition": cond}
        if reference:
            entry["reference"] = True
        entries.append(entry)
    return {"id": test_id, "title": title, "question": question, "notes": notes, "clips": entries,
            "questions": questions}


def bright_db(x):
    s = np.abs(np.fft.rfft(dl.mono(x))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / dl.SR)
    return 10 * np.log10(s[f > 1500].sum() / s.sum())


VARIANTS = [
    ("now", "Now", "The flute profile as it is ('h-u', every note re-articulated)", []),
    ("nof3", "No F3", "The monk's third formant (2.2-2.9 kHz) off", NO_F3),
    ("nof3_dark", "No F3, less breath", "F3 off and breath 0.3 (was 0.75)", NO_F3 + DARK),
    ("nof3_legato", "No F3, slurs legato", "F3 off; slurred notes glide quickly instead of "
     "re-articulating", NO_F3 + LEGATO),
    ("nof3_dark_legato", "No F3, less breath, legato", "All three changes", NO_F3 + DARK + LEGATO),
]


def melody(report):
    ref = gervill("melody")
    target = lufs(ref)
    report += ["## melody/", "",
               f"Gervill: {target:.1f} LUFS; energy above 1.5 kHz {bright_db(ref):+.1f} dB of the total. "
               f"The monk sings {fp.shift_of(fp.melody()):+d} st (the octave fold).", "",
               "| Clip | Natural loudness (LUFS) | vs Gervill (dB) | Above 1.5 kHz (dB of total) | Peak after matching |",
               "| --- | --- | --- | --- | --- |"]
    clips = [("gervill", "Gervill", "What midis2jam2 plays (reference)", True, ref)]
    for cond, label, desc, extra in VARIANTS:
        x = render(f"melody_{cond}", fp.melody(), extra)
        y = match(x, target)
        report.append(f"| {cond} | {lufs(x):.1f} | {lufs(x) - target:+.1f} | {bright_db(x):+.1f} | "
                      f"{20 * np.log10(np.abs(y).max()):.1f} dBFS |")
        clips.append((cond, label, desc, False, y))
    report.append("")
    conds = [(c[0], c[1]) for c in clips if not c[3]]
    questions = [
        {"id": "best", "text": BEST, "multi": False,
         "choices": choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
        {"id": "flute", "text": "Which could pass for a flute imitation at all?", "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "glitch", "text": GLITCH, "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "slurs", "text": "Which slurred notes (pairs, the climb, the run down) sound right?",
         "multi": True, "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
    ]
    return clip_set(
        "melody", "Flute melody: buzz, breath and slurs",
        "Eight bars of flute melody alone (slurred pairs, tongued notes, a climb, a fast run "
        "down): which sounds most like a flute imitation?",
        "Your phase 4a note: 'not like a flute at all, more like a plucked laser gun'. That "
        "clip's laser was a vowel jump on every tongued note, which the profile no longer has; "
        "this is the articulator's flute, never heard before. Measured: the monk is buzzy where a "
        "flute is nearly a pure tone, because its third formant (2.2-2.9 kHz) lifts whichever "
        "harmonic meets it, sometimes above the note itself. 'No F3' switches that formant off "
        "(new helper key). 'Less breath' turns down the breath partials (3.8 and 5 kHz). "
        "'Legato' glides quickly through slurred notes instead of tonguing each one. The melody "
        "is written around B5 and sung an octave lower (your octave fold). Every clip at Gervill's "
        "loudness; blind mode is worth it.",
        clips, questions)


def band(report):
    full = gervill("band")
    rest = gervill("band_no_flute")
    flute = gervill("melody")
    target = lufs(full)
    report += ["## band/", "",
               f"Gervill: the full band {target:.1f} LUFS, its flute alone {lufs(flute):.1f} LUFS, "
               f"the band without flute {lufs(rest):.1f} LUFS. Live mix: the band without flute "
               f"{BALANCE_DB:g} dB down (the live balance) plus the helper at its own level (CC7 100, the file's "
               "velocities, gain 1), then the whole mix at the full band's loudness.", "",
               "| Clip | Monk alone (LUFS) | Monk vs Gervill's flute (dB) | Mix gain |",
               "| --- | --- | --- | --- |"]
    picks = [v for v in VARIANTS if v[0] in ("now", "nof3_legato", "nof3_dark_legato")]
    clips = [("gervill", "Gervill only", "What midis2jam2 plays without Delay Lama", True, full)]
    now_level = None
    for cond, label, desc, extra in picks:
        monk = render(f"band_{cond}", fp.melody(), extra)
        if now_level is None:
            now_level = lufs(monk)
        else:  # dyn.gain brings the candidate to the profile's level now (F3 off is quieter)
            gain = round(10 ** ((now_level - lufs(monk)) / 20) / 0.05) * 0.05
            extra = extra + [("dyn.gain", gain)]
            monk = render(f"band_{cond}", fp.melody(), extra)
            desc += f" (dyn.gain {gain:g}, to the level the profile has now)"
        n = max(len(rest), len(monk))
        mix = pad(rest, n) * 10 ** (-BALANCE_DB / 20) + pad(monk, n)
        y = match(mix, target)
        report.append(f"| {cond} | {lufs(monk):.1f} | {lufs(monk) - lufs(flute):+.1f} | "
                      f"{target - lufs(mix):+.1f} dB |")
        clips.append((cond, label, desc, False, y))
    report.append("")
    conds = [(c[0], c[1]) for c in clips if not c[3]]
    questions = [
        {"id": "best", "text": "Which works best as the flute in the band?", "multi": False,
         "choices": choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
        {"id": "heard", "text": "In which can you hear the flute well enough?", "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "glitch", "text": GLITCH, "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
    ]
    return clip_set(
        "band", "Flute in a small band",
        "String pad, bass and drums from Gervill, the flute sung: which works best, and can you "
        "hear it?",
        "Mixed as live playback plays it: Gervill 6 dB down (your live balance), the monk at its "
        "own level, every mix at the same loudness. 'Now' is the profile as it is; the two "
        "candidates have F3 off and legato slurs, with and without less breath. F3 off makes the "
        "monk 4-5 dB quieter, so the candidates get a new level key (dyn.gain) that brings them "
        "back to the level 'Now' has.",
        clips, questions)


def main():
    for d in (TMP, SCRIPTS):
        d.mkdir(exist_ok=True)
    fp.write_all_midi()
    report = ["# Pipe round 1: levels", "",
              "Written by `make_4c_pipe.py`. Loudness by ITU-R BS.1770 (gated, LUFS).", ""]
    tests = [melody(report), band(report)]
    manifest = {
        "format": 1,
        "title": "Flute, round 1: buzz, breath, slurs",
        "intro": "The second family. Your phase 4a flute was 'a plucked laser gun'; its laser is "
                 "gone from the profile. Measured: the monk's flute is much buzzier than Gervill's, "
                 "from its third formant, and a new helper key turns that formant off. Two tests: "
                 "the melody alone, and in a small band at your live balance.",
        "tests": tests,
    }
    (WORK / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (WORK / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    shutil.rmtree(TMP)
    print("\n".join(report))
    print("wrote", sum(len(t["clips"]) for t in tests), "clips")


if __name__ == "__main__":
    main()
