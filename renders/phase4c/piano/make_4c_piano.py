"""Phase 4c, piano family (GM programs 1-8, profile `piano`): the first 4c
tuning set (IMITATION.md 16-17; c02's "broken detune piano").

What the measurements (measure_4c_piano.py, measure/measurements.md) found:
- The DSP's per-note tuning error is small and smooth: +2 to +5 cents from C3
  to A4, +9 to +11 at C5-D#5, so chord notes agree within 1-2 cents on
  average. No bend correction.
- The "detune" is the vibrato floor: every monk wobbles +-0.2 st on its own
  (own seeds since phase 4b, D17), so a chord's intervals swing by ~75 cents
  (sd ~20). choir.vibrato_var changes nothing. One shared seed holds them only
  while the monks' histories match (not after a melody or in an arpeggio). The
  helper's new `vibrato.lock` (a new note takes over the LFO of a monk that
  sings) holds every interval within 8-15 cents in all three cases.
- Decay: the profile's note is gone 1.4 s after a C4 starts; Gervill's piano
  is -15 dB at 1 s and -29 dB at 3 s. Decay 2500 ms with track 0.85 is close.
- The body drift (i -> e over 600 ms) bends that decay: notes swell by up to
  6-10 dB or dip by 5-6 dB as the vowel crosses harmonics; a steady vowel
  stays within about 2-3 dB ("e" the evenest).
- The "ng" ending's vowel sweep lifts some harmonic 24-43 dB above where it
  was (1-24 dB without it), and at E5 and G#5 the whole note gets louder as
  it ends (+2.4 and +8.8 dB): onset moves glitched the same way (D33).

Three tests (14 clips):
1. chords/: the piano part alone (block chords, pedalled arpeggios, a long
   chord), 4 monks: now, locked, locked with the longer decay.
2. lines/: scale, repeated notes, a legato line, a fast run and a long C4:
   now, longer decay, longer without the "ng", longer on a steady "e" (the
   i>e drift swells or dips notes by 5-10 dB, measured), longer with a bigger
   voice (0.4).
3. band/: drums and bass (Gervill) with the sung piano part, mixed as live
   playback plays it (Gervill 6 dB down, D36; the monks at their own level):
   now with 4 monks, and the locked, longer candidate with 4 and 6 monks (the
   part never has more than six notes ringing, so 8 monks would only move the
   stereo places).

Every clip is matched to Gervill's integrated loudness (ITU-R BS.1770, gated),
not to the active RMS of rounds 3-6: a longer decay adds quiet tail, which a
plain RMS counts against the note (report.md has both).

Run: py renders/phase4c/piano/make_4c_piano.py  (writes renders/phase4c/piano/)
"""

import json
import pathlib
import shutil
import sys

import numpy as np
from scipy.signal import lfilter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import piano_phrases as pp  # noqa: E402
from piano_phrases import dl  # noqa: E402

SR = dl.SR
TMP = HERE / "tmp"
SCRIPTS = HERE / "scripts"
BALANCE_DB = 6.0  # D34/D36: Gervill's line 6 dB down while a channel is sung

LOCK = [("vibrato.lock", 1)]
LONG = [("body.decay", 2500), ("body.decay_track", 0.85)]
OPEN = [("ending.vowel", -1)]
BIG = [("voice.size", 0.4)]
STEADY_E = [("nucleus.vowel", 0.75), ("body.vowel", -1)]

GLITCH = "Which clips have a glitch (laser, high pitch at a start, whistle, click, wobble)?"
BEST = "Which sounds most like someone imitating a piano?"
DETUNED = "Which sound out of tune or detuned?"


# --- Loudness ---------------------------------------------------------------------

def lufs(x):
    """Integrated loudness (ITU-R BS.1770-4) of a 48 kHz stereo signal:
    K-weighting, 400 ms blocks every 100 ms, absolute gate -70 LUFS, relative
    gate -10 LU."""
    shelf_b = [1.53512485958697, -2.69169618940638, 1.19839281085285]
    shelf_a = [1.0, -1.69065929318241, 0.73248077421585]
    hp_b = [1.0, -2.0, 1.0]
    hp_a = [1.0, -1.99004745483398, 0.99007225036621]
    y = lfilter(hp_b, hp_a, lfilter(shelf_b, shelf_a, x, axis=0), axis=0)
    block, step = int(0.4 * SR), int(0.1 * SR)
    power = np.array([np.mean(y[i:i + block] ** 2, axis=0).sum()
                      for i in range(0, max(1, len(y) - block), step)])
    loud = -0.691 + 10 * np.log10(power + 1e-20)
    kept = power[loud > -70]
    if not len(kept):
        return -70.0
    relative = -0.691 + 10 * np.log10(kept.mean()) - 10
    kept = power[(loud > -70) & (loud > relative)]
    return float(-0.691 + 10 * np.log10(kept.mean()))


def active_rms_db(x, floor=1e-4):
    """Round 3's measure, for the report: RMS of the samples that sound."""
    mono = x.mean(axis=1)
    sounding = mono[np.abs(mono) > floor]
    return 20 * np.log10(np.sqrt((sounding ** 2).mean())) if len(sounding) else -120.0


def match(x, target_lufs):
    return x * 10 ** ((target_lufs - lufs(x)) / 20)


def pad(x, n):
    return np.vstack([x, np.zeros((n - len(x), 2))]) if len(x) < n else x[:n]


# --- Rendering --------------------------------------------------------------------

def render(name, phrase, extra=(), monks=4):
    text = pp.script(phrase, pp.profile(), extra)
    path = SCRIPTS / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return dl.render(path, monks=monks, tail=1500)


def gervill(name):
    return pp.gervill(HERE / "midi" / f"{name}.mid", TMP / f"{name}.wav")


def choices(conds, extra=()):
    return [{"id": c, "label": label, "condition": c} for c, label in conds] + list(extra)


def clip_set(test_id, title, question, notes, clips, questions):
    """clips: (condition, label, desc, reference, signal), already
    loudness-matched. One gain for the test (peak 0.89), same length."""
    folder = HERE / test_id
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir()
    n = max(len(x) for *_, x in clips)
    scale = 0.89 / max(np.abs(x).max() for *_, x in clips)
    entries = []
    for k, (cond, label, desc, reference, x) in enumerate(clips, 1):
        name = f"{test_id}/{k:02d}_{cond}.wav"
        dl.write_wav(HERE / name, pad(x, n) * scale)
        entry = {"file": name, "label": label, "desc": desc, "condition": cond}
        if reference:
            entry["reference"] = True
        entries.append(entry)
    return {"id": test_id, "title": title, "question": question, "notes": notes, "clips": entries,
            "questions": questions}


def solo_test(report, test_id, title, question, notes, midi, phrase, variants, extra_questions):
    ref = gervill(midi)
    target = lufs(ref)
    report += [f"## {test_id}/", "", f"Gervill: {target:.1f} LUFS, active RMS {active_rms_db(ref):.1f} dB.",
               "", "| Clip | Natural loudness (LUFS) | Gain to Gervill (LUFS / active RMS, dB) | Peak after |",
               "| --- | --- | --- | --- |"]
    clips = [("gervill", "Gervill", "What midis2jam2 plays (reference)", True, ref)]
    for cond, label, desc, extra in variants:
        x = render(f"{test_id}_{cond}", phrase, extra)
        y = match(x, target)
        report.append(f"| {cond} | {lufs(x):.1f} | {target - lufs(x):+.1f} / "
                      f"{active_rms_db(ref) - active_rms_db(x):+.1f} | "
                      f"{20 * np.log10(np.abs(y).max()):.1f} dBFS |")
        clips.append((cond, label, desc, False, y))
    report.append("")
    conds = [(c[0], c[1]) for c in clips if not c[3]]
    questions = [{**q, "choices": choices(conds, q["choices"])} for q in extra_questions]
    questions += [
        {"id": "glitch", "text": GLITCH, "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "best", "text": BEST, "multi": False,
         "choices": choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
    ]
    return clip_set(test_id, title, question, notes, clips, questions)


def chords(report):
    return solo_test(
        report, "chords", "Piano chords: in tune?",
        "Piano part alone (block chords, pedalled arpeggios, a long chord), 4 monks: which sound "
        "out of tune or detuned?",
        "Each monk's vibrato floor (±0.2 st, the wobble that keeps Delay Lama alive) runs on its "
        "own, so the intervals of a chord swing by up to ~75 cents. 'Locked' makes every monk of a "
        "chord wobble together (new helper key vibrato.lock), so the intervals stay within ~10 "
        "cents and the chord wobbles as one. The tuning between notes is only 1-2 cents off "
        "(measured), so nothing else changes. Every clip at Gervill's loudness; blind mode is "
        "worth it.",
        "piano_part", pp.piano_part(),
        [("now", "Now", "The piano profile as it is: each monk wobbles on its own", []),
         ("locked", "Locked", "vibrato.lock: the monks of a chord wobble together", LOCK),
         ("locked_long", "Locked, longer", "Locked, and notes ring about as long as Gervill's "
          "(decay 2.5 s at C4)", LOCK + LONG)],
        [{"id": "detuned", "text": DETUNED, "multi": True,
          "choices": [{"id": "none", "label": "None of them"}]}])


def lines(report):
    return solo_test(
        report, "lines", "Piano lines: decay, ending and voice",
        "Scale, repeated notes, a legato line, a fast run and a long C4: which sounds most like "
        "a piano imitation?",
        "Now: a note is gone 1.4 s after it starts (at C4; Gervill's piano is still only 29 dB "
        "down at 3 s) and closes on 'ng' when the key lifts. 'Longer' rings about as long as "
        "Gervill's (decay 2.5 s at C4, a little shorter up high). 'No ng' keeps the vowel as it "
        "is while the note fades. 'Steady e' sings 'e' all through instead of drifting from 'i' to "
        "'e' (measured: the drift makes some notes swell or dip by 5-10 dB as they ring, since "
        "the moving vowel crosses the harmonics). 'Bigger voice' is voice size 0.4 instead of "
        "0.6 (a larger, darker head). One line, so the vibrato lock makes no difference here. Every clip at "
        "Gervill's loudness.",
        "lines", pp.lines(),
        [("now", "Now", "The piano profile as it is (d-i>e-ng, decay 0.9 s at C4)", []),
         ("long", "Longer", "Decay 2.5 s at C4 (track 0.85 per octave)", LONG),
         ("long_open", "Longer, no ng", "Longer, and no 'ng' when the key lifts", LONG + OPEN),
         ("long_e", "Longer, steady 'e'", "Longer, sung on 'e' throughout (no i-to-e drift)",
          LONG + STEADY_E),
         ("long_big", "Longer, bigger voice", "Longer, voice size 0.4", LONG + BIG)],
        [{"id": "ring", "text": "Which ring about the right length?", "multi": True,
          "choices": [{"id": "too_short", "label": "None: all too short"},
                      {"id": "too_long", "label": "None: all too long"}]},
         {"id": "ending", "text": "Which note endings (when the key lifts) sound right?",
          "multi": True, "choices": [{"id": "none", "label": "None of them"}]}])


def band(report):
    full = gervill("band")
    rest = gervill("band_no_piano")
    piano = gervill("piano_part")
    target = lufs(full)
    report += ["## band/", "",
               f"Gervill: the full band {target:.1f} LUFS, its piano alone {lufs(piano):.1f} LUFS, "
               f"the band without piano {lufs(rest):.1f} LUFS. Live mix: the band without piano "
               f"{BALANCE_DB:g} dB down (D36) plus the helper at its own level (CC7 100, velocities "
               "from the file, gain 1), then the whole mix at the full band's loudness.", "",
               "| Clip | Monks alone (LUFS) | Monks vs Gervill's piano (dB) | Live mix peak before matching | Mix gain |",
               "| --- | --- | --- | --- | --- |"]
    variants = [
        ("now_4", "Now, 4 monks", "The piano profile as it is, 4 monks (the default)", [], 4),
        ("cand_4", "Candidate, 4 monks", "Locked and longer, 4 monks", LOCK + LONG, 4),
        ("cand_6", "Candidate, 6 monks", "Locked and longer, 6 monks", LOCK + LONG, 6),
    ]
    clips = [("gervill", "Gervill only", "What midis2jam2 plays without Delay Lama", True, full)]
    for cond, label, desc, extra, monks in variants:
        monk = render(f"band_{cond}", pp.piano_part(), extra, monks)
        n = max(len(rest), len(monk))
        mix = pad(rest, n) * 10 ** (-BALANCE_DB / 20) + pad(monk, n)
        y = match(mix, target)
        report.append(f"| {cond} | {lufs(monk):.1f} | {lufs(monk) - lufs(piano):+.1f} | "
                      f"{20 * np.log10(np.abs(mix).max()):.1f} dBFS | {target - lufs(mix):+.1f} dB |")
        clips.append((cond, label, desc, False, y))
    report.append("")
    conds = [(c[0], c[1]) for c in clips if not c[3]]
    questions = [
        {"id": "best", "text": "Which works best as the piano in the band?", "multi": False,
         "choices": choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
        {"id": "detuned", "text": DETUNED, "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "heard", "text": "In which can you hear the piano well enough?", "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "glitch", "text": GLITCH, "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
    ]
    return clip_set(
        "band", "Piano in a small band",
        "Drums and bass from Gervill, the piano part sung: which works best as the piano?",
        "Mixed as live playback plays it: Gervill 6 dB down (your D34 balance), the monks at their "
        "own level; every mix at the same loudness. 'Now' is the profile as it is. The candidate "
        "is locked and rings longer (the changes in the other two tests), with 4 or 6 monks: "
        "a pedalled arpeggio has up to six notes ringing, and with 4 monks the oldest "
        "pedal-held notes (the bass of each arpeggio first) are cut.",
        clips, questions)


def main():
    for d in (TMP, SCRIPTS):
        d.mkdir(exist_ok=True)
    pp.write_all_midi()
    report = ["# Phase 4c piano set: levels", "",
              "Written by `make_4c_piano.py`. Loudness by ITU-R BS.1770 (gated, LUFS).", ""]
    tests = [chords(report), lines(report), band(report)]
    manifest = {
        "format": 1,
        "title": "Phase 4c piano: in tune, ringing, in the band",
        "intro": "The first family tuning set. Your c02 note said the piano choir 'sounds like a "
                 "broken detune piano'. Measured: the notes themselves are in tune within a few "
                 "cents, but every monk's small vibrato runs on its own, so a chord's intervals "
                 "keep swinging. A new helper key locks the monks of a chord together. The "
                 "piano notes also die much sooner than Gervill's. Three tests: chords, single "
                 "lines, and the piano in a small band at your live balance.",
        "tests": tests,
    }
    (HERE / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (HERE / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    shutil.rmtree(TMP)
    print("\n".join(report))
    print("wrote", sum(len(t["clips"]) for t in tests), "clips")


if __name__ == "__main__":
    main()
