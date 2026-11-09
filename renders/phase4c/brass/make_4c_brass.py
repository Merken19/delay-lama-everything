"""Phase 4c, brass and sax families (GM 57-68; profiles `trumpet`,
`sax.tenor`, and for measurement only `trombone`, `tuba`, `brass.section`,
`sax.alto`), round 1 (IMITATION.md 16-17). The user's 4a remarks: trumpet c03
"very good; an occasional very high pitch", sax c04 "too bright for a tenor
sax".

What the measurements found (measure_4c_brass.py, measure/measurements.md):
- Trumpet: the DSP's two breath partials (3.80 and 4.95 kHz, fixed damped
  sines in every grain, so two narrow resonances) lift the harmonic that meets
  them. At A4 the 11th harmonic (4.84 kHz) stands 18-19 dB above its
  neighbours, about -16 dB under the note's loudest harmonic (Gervill: -28);
  over the whole line the breath band sits ~12 dB higher against the note than
  in Gervill's trumpet. The profile's breath is 0.75 all through the note (its
  0.6 burst is a dip, not a puff); c03 had breath 0.45 with a 1.0 burst at
  each onset, so its whistle came at onsets ("occasional"). Breath 0.3 puts
  the band at Gervill's level (A4 -23..-27 dB, E5 -18..-20); only no breath
  removes the ring. F3 off makes it worse (the trumpet needs its 2-3 kHz).
- Tenor sax: overall no brighter than Gervill's tenor (same share above
  1.6 kHz), but shaped differently: 13 dB too little at 800-1600 Hz, where a
  tenor's warmth is, and the DSP's F3 (2.2-2.9 kHz, as loud as F1 and F2)
  standing alone above that hole, which reads as thin and bright.
  voice.formant3 0.6 (F3's frequencies times 0.6, so 1.3-1.7 kHz) fills the
  hole: the octave bands match Gervill's within 1 dB from 400 Hz to 1.6 kHz
  and the mean centroid is 1034 Hz (Gervill 1099, now 1385). F3 off is far
  darker than Gervill (centroid 648).
- sax.tenor inherits the alto's attack and ending only on paper: its own
  syllable resets them (attack 3 instead of 20, release 20 instead of 120,
  no "o" ending), an accident of the profile data.
- Levels: trumpet -0.9 dB, tenor -4.6 dB against Gervill's instrument.

Three tests (16 clips), every clip in a test at Gervill's loudness (ITU-R
BS.1770) except the band, which is mixed as live playback plays it:
1. trumpet/: eight bars of tongued trumpet lead (A4 and E5 onsets): now,
   breath 0.45, 0.3, 0.3 with a 0.6 burst at each onset, and none.
2. sax/: eight bars of tenor sax: now, F3 x0.6, F3 x0.6 with breath 0.3, F3
   off with breath 0.3, and F3 x0.6 with breath 0.3 and the sax attack and
   ending the profile was meant to have.
3. band/: trumpet and tenor sax trading two-bar phrases over Gervill's
   electric piano, bass and drums, Gervill 6 dB down (D36): Gervill only, now,
   and two darker pairs, each monk brought to the level it has now with
   dyn.gain (D49), so only the sound differs.

Run: py renders/phase4c/brass/make_4c_brass.py  (writes renders/phase4c/brass/)
"""

import json
import pathlib
import shutil
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import brass_phrases as bp  # noqa: E402
from brass_phrases import dl, pp  # noqa: E402

sys.path.insert(0, str(HERE.parent / "piano"))
from make_4c_piano import lufs, match, pad, choices  # noqa: E402

TMP = bp.TMP
SCRIPTS = HERE / "scripts"
BALANCE_DB = 6.0

GLITCH = "Which clips have a glitch (a high pitch or whistle above the note, laser, click, wobble)?"


def breath(b, burst=None):
    return [("body.breath", b), ("onset.burst", b if burst is None else burst)]


F3_LOW = [("voice.formant3", 0.6)]
F3_OFF = [("voice.formant3", 0)]
SAX_FIX = [("onset.attack", 20), ("ending.release", 120), ("ending.vowel", 0.25)]

TRUMPET = [
    ("now", "Now", "The trumpet profile as it is ('t-a', breath 0.75 all through)", []),
    ("breath045", "Breath 0.45", "Less breath (c03's amount), no puff at the onsets", breath(0.45)),
    ("breath03", "Breath 0.3", "Breath 0.3, no puff at the onsets", breath(0.3)),
    ("breath03_puff", "Breath 0.3, puff", "Breath 0.3 with a 0.6 puff at each onset (falls in 30 ms)",
     breath(0.3, 0.6)),
    ("nobreath", "No breath", "No breath at all", breath(0)),
]

SAX = [
    ("now", "Now", "The tenor sax profile as it is ('d-u>o', breath 0.6)", []),
    ("f3low", "F3 lower", "The third formant moved down (x0.6: 2.2-2.9 kHz to 1.3-1.7 kHz)", F3_LOW),
    ("f3low_b03", "F3 lower, breath 0.3", "F3 x0.6 and breath 0.3", F3_LOW + breath(0.3)),
    ("f3off_b03", "F3 off, breath 0.3", "No third formant, breath 0.3 (the darkest)", F3_OFF + breath(0.3)),
    ("f3low_b03_fix", "F3 lower, breath 0.3, sax ending", "As 'F3 lower, breath 0.3', with the softer "
     "attack (20 ms) and the 'o' release over 120 ms the sax profiles were meant to have", F3_LOW +
     breath(0.3) + SAX_FIX),
]

BAND = [
    ("now", "Now", "Both profiles as they are", [], []),
    ("darker", "Darker", "Trumpet breath 0.3; sax F3 lower, breath 0.3", breath(0.3), F3_LOW + breath(0.3)),
    ("darkest", "Darkest", "Trumpet without breath; sax F3 off, breath 0.3", breath(0),
     F3_OFF + breath(0.3)),
]


def render(name, phrase, profile, extra=()):
    text = bp.script(phrase, bp.profile(profile), extra)
    path = SCRIPTS / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return dl.render(path, monks=1, tail=800)


def gervill(name):
    return pp.gervill(HERE / "midi" / f"{name}.mid", TMP / f"{name}.wav")


def clip_set(test_id, title, question, notes, clips, questions):
    """clips: (condition, label, desc, reference, signal). One gain per test
    (peak 0.89), every clip the same length."""
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


def band_db(x, lo, hi):
    p = np.abs(np.fft.rfft(dl.mono(x))) ** 2
    f = np.fft.rfftfreq(len(dl.mono(x)), 1 / dl.SR)
    return 10 * np.log10(p[(f >= lo) & (f < hi)].sum() / p.sum())


def solo(report, test_id, midi, profile, variants):
    ref = gervill(midi)
    target = lufs(ref)
    report += [f"## {test_id}/", "",
               f"Gervill: {target:.1f} LUFS; 800-1600 Hz {band_db(ref, 800, 1600):+.1f} dB, above "
               f"1.6 kHz {band_db(ref, 1600, 24000):+.1f} dB, 3.5-5.5 kHz {band_db(ref, 3500, 5500):+.1f} dB "
               "of the total.", "",
               "| Clip | Natural loudness (LUFS) | vs Gervill (dB) | 800-1600 Hz | Above 1.6 kHz | 3.5-5.5 kHz "
               "| Peak after matching |", "| --- | --- | --- | --- | --- | --- | --- |"]
    clips = [("gervill", "Gervill", "What midis2jam2 plays (reference)", True, ref)]
    for cond, label, desc, extra in variants:
        x = render(f"{test_id}_{cond}", getattr(bp, midi)(), profile, extra)
        y = match(x, target)
        report.append(f"| {cond} | {lufs(x):.1f} | {lufs(x) - target:+.1f} | {band_db(x, 800, 1600):+.1f} | "
                      f"{band_db(x, 1600, 24000):+.1f} | {band_db(x, 3500, 5500):+.1f} | "
                      f"{20 * np.log10(np.abs(y).max()):.1f} dBFS |")
        clips.append((cond, label, desc, False, y))
    report.append("")
    return clips


def trumpet_test(report):
    clips = solo(report, "trumpet", "trumpet", "trumpet", TRUMPET)
    conds = [(c[0], c[1]) for c in clips if not c[3]]
    questions = [
        {"id": "best", "text": "Which sounds most like someone imitating a trumpet?", "multi": False,
         "choices": choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
        {"id": "high", "text": "In which do you hear the very high pitch (a thin whistle above the note; "
         "the A4s and E5s are where it was measured)?", "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "dull", "text": "Which are too dull or too pure for a trumpet?", "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "glitch", "text": GLITCH, "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
    ]
    return clip_set(
        "trumpet", "Trumpet: the high pitch and the breath",
        "Eight bars of tongued trumpet lead alone: which sounds most like a trumpet imitation, and "
        "where is the very high pitch?",
        "Your phase 4a note on c03: 'very good; an occasional very high pitch'. Measured: the monk's "
        "breath is two fixed high partials (3.8 and 5 kHz) that make whichever harmonic meets them "
        "ring, most on the A4s (its 11th harmonic, 4.8 kHz, stands out by 18 dB). The profile "
        "breathes at 0.75 all through each note; c03 breathed at 0.45 with a strong puff at each "
        "onset. Less breath makes the whistle quieter (0.3 is about Gervill's level); only 'no "
        "breath' removes it, and may sound too pure. Sung as written (A4-F5 sit within your D37 "
        "range). Every clip at Gervill's loudness; blind mode is worth it.",
        clips, questions)


def sax_test(report):
    clips = solo(report, "sax", "sax", "sax.tenor", SAX)
    conds = [(c[0], c[1]) for c in clips if not c[3]]
    questions = [
        {"id": "best", "text": "Which sounds most like someone imitating a tenor sax?", "multi": False,
         "choices": choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
        {"id": "bright", "text": "Which are still too bright for a tenor sax?", "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "dull", "text": "Which are too dull or muffled?", "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "glitch", "text": GLITCH, "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
    ]
    return clip_set(
        "sax", "Tenor sax: brightness",
        "Eight bars of tenor sax alone (mostly slurred, E3-G4): which sounds most like a tenor sax "
        "imitation?",
        "Your phase 4a note on c04: 'too bright, wouldn't use this for a tenor sax'. The profile is "
        "already darker than c04 was (u drifting to o instead of to a, a bigger voice). Measured: "
        "it is no brighter than Gervill's tenor overall, but it misses the warm middle (800-1600 "
        "Hz) and its third formant (2.2-2.9 kHz) stands alone above that hole. 'F3 lower' moves that "
        "formant down into the hole (the closest match to Gervill's spectrum); 'F3 off' removes it "
        "(darker than Gervill); less breath turns down the two high breath partials. The last clip "
        "also gives the tenor the softer attack and the longer 'o' release the sax profiles were "
        "meant to have (the tenor lost them by accident). Every clip at Gervill's loudness.",
        clips, questions)


def band_test(report):
    full = gervill("band")
    rest = gervill("band_rest")
    g_tp, g_sx = gervill("band_trumpet"), gervill("band_sax")
    target = lufs(full)
    report += ["## band/", "",
               f"Gervill: the full band {target:.1f} LUFS, its trumpet alone {lufs(g_tp):.1f}, its tenor "
               f"alone {lufs(g_sx):.1f}, the band without them {lufs(rest):.1f} LUFS. Live mix: the band "
               f"without horns {BALANCE_DB:g} dB down (D36) plus each helper at its own level (CC7 100, "
               "the file's velocities, gain 1), then the whole mix at the full band's loudness.", "",
               "| Clip | Trumpet monk (LUFS, vs Gervill's) | Sax monk (LUFS, vs Gervill's) | Mix gain |",
               "| --- | --- | --- | --- |"]
    clips = [("gervill", "Gervill only", "What midis2jam2 plays without Delay Lama", True, full)]
    level = {}
    for cond, label, desc, tp_extra, sx_extra in BAND:
        monks = []
        for part, phrase, prof, extra in (("trumpet", bp.band_trumpet(), "trumpet", tp_extra),
                                          ("sax", bp.band_sax(), "sax.tenor", sx_extra)):
            x = render(f"band_{cond}_{part}", phrase, prof, extra)
            if part in level and abs(lufs(x) - level[part]) > 0.2:
                # dyn.gain (D49) brings a darker candidate to the level the profile has now
                gain = round(10 ** ((level[part] - lufs(x)) / 20), 3)
                x = render(f"band_{cond}_{part}", phrase, prof, list(extra) + [("dyn.gain", gain)])
                desc += f"; {part} dyn.gain {gain:g}"
            level.setdefault(part, lufs(x))
            monks.append(x)
        tp, sx = monks
        n = max(len(rest), len(tp), len(sx))
        mix = pad(rest, n) * 10 ** (-BALANCE_DB / 20) + pad(tp, n) + pad(sx, n)
        y = match(mix, target)
        report.append(f"| {cond} | {lufs(tp):.1f} ({lufs(tp) - lufs(g_tp):+.1f}) | {lufs(sx):.1f} "
                      f"({lufs(sx) - lufs(g_sx):+.1f}) | {target - lufs(mix):+.1f} dB |")
        clips.append((cond, label, desc, False, y))
    report.append("")
    conds = [(c[0], c[1]) for c in clips if not c[3]]
    questions = [
        {"id": "best", "text": "Which works best as the horns of this band?", "multi": False,
         "choices": choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
        {"id": "trumpet", "text": "In which does the trumpet (bars 1-2 and 5-6) sound right?", "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "sax", "text": "In which does the tenor sax (bars 3-4 and 7-8) sound right?", "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "glitch", "text": GLITCH, "multi": True,
         "choices": choices(conds, [{"id": "none", "label": "None of them"}])},
    ]
    return clip_set(
        "band", "Trumpet and tenor sax in a band",
        "Trumpet and tenor sax trade two-bar phrases over Gervill's electric piano, bass and drums: "
        "which pair works best?",
        "Mixed as live playback plays it: Gervill 6 dB down (your D34 balance), each monk at its own "
        "level, every mix at the same loudness. The trumpet plays bars 1-2 and 5-6, the sax bars 3-4 "
        "and 7-8. 'Darker': trumpet breath 0.3, sax F3 lower and breath 0.3 (the measured closest to "
        "Gervill). 'Darkest': trumpet without breath, sax F3 off and breath 0.3. The darker monks "
        "come out quieter, so a level key (dyn.gain) brings each back to the level it has now; "
        "only the sound differs.",
        clips, questions)


def main():
    for d in (TMP, SCRIPTS):
        d.mkdir(exist_ok=True)
    bp.use_exe_copy()
    bp.write_all_midi()
    report = ["# Phase 4c brass round 1: levels and bands", "",
              "Written by `make_4c_brass.py`. Loudness by ITU-R BS.1770 (gated, LUFS); bands in dB of "
              "each clip's total energy.", ""]
    tests = [trumpet_test(report), sax_test(report), band_test(report)]
    manifest = {
        "format": 1,
        "title": "Phase 4c brass, round 1: the trumpet's high pitch, the tenor's brightness",
        "intro": "The third family. Your phase 4a notes: the trumpet was 'very good' with 'an occasional "
                 "very high pitch', the tenor sax 'too bright'. Measured: the trumpet's high pitch is "
                 "the monk's breath ringing on a harmonic (less breath quiets it), and the tenor misses a "
                 "sax's warm middle while its third formant stands out (moving that formant down fills "
                 "it). Three tests: trumpet alone, tenor sax alone, both in a small band at your live "
                 "balance.",
        "tests": tests,
    }
    (HERE / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (HERE / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    shutil.rmtree(TMP)
    print("\n".join(report))
    print("wrote", sum(len(t["clips"]) for t in tests), "clips")


if __name__ == "__main__":
    main()
