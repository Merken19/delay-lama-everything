"""Phase 4b, round 4 (after the user's answers in renders/phase4b/round3/answers.md).

Round 3: wider formants removed the bass laser only at x4, and the 'doo' went
with it; only phase 4a's clip had the 'doo', and it was still the best bass.
The articulator's 'd' (0.55 -> u over 50 ms) had no 'doo' even with narrow
formants, so the 'doo' comes from something else phase 4a's DUM did. This
round walks from the articulator towards phase 4a's DUM one difference at a
time (nucleus 'oo' instead of 'u', 25 ms move, no attack, breath 0.25), then
tries to keep that 'doo' while softening the laser.

The violin was clean an octave lower, so high parts now fold down by default
(D37, range.fit 2: down by octaves while the channel's median is above C5).
The violin and K525's violin 1 are rendered with the new default, legato and
without glides.

Run: py renders/phase4b/make_4b4.py  (writes renders/phase4b/round4/)
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = sys.argv[:1]
import make_4b  # noqa: E402
import make_4b3  # noqa: E402
from make_4b import make_ab, dl, expand  # noqa: E402

OUT = HERE / "round4"
make_4b.HERE = OUT  # clip_set and render write under round4/
make_4b3.OUT = OUT

# Phase 4a's DUM (renders/phase4a/ab/make_ab.py) in articulator keys.
DUM = [("nucleus.vowel", 0.12), ("onset.vowel", 0.55), ("onset.time", 25), ("onset.attack", 0),
       ("body.breath", 0.25)]


def bass():
    return make_4b3.test(
        "bass", "Bass: finding phase 4a's 'doo'",
        "Bass: which have the 'doo', and which have the laser?",
        "Round 3: only phase 4a had the 'doo', and the articulator's 'd' had none even with "
        "Delay Lama's own formants. 'Like 4a' is phase 4a's settings in the articulator (nucleus "
        "'oo', a 25 ms move from 0.55, no attack, breath 0.25); the others change one thing "
        "from it. Every clip at the same loudness.",
        "bass.finger", make_ab.bass_line(),
        [("steady", "Steady (default)", "No onset vowel move", []),
         ("like4a", "Like 4a", "Phase 4a's settings in the articulator", DUM),
         ("like4a_u", "Like 4a, 'u' nucleus", "The same, with the profile's 'u' instead of 'oo'",
          DUM + [("nucleus.vowel", 0)]),
         ("like4a_small", "Like 4a, smaller move", "Onset from 0.35 instead of 0.55",
          DUM + [("onset.vowel", 0.35)]),
         ("like4a_step", "Like 4a, short step", "Hold 0.55 for 10 ms, then step to 'oo'",
          DUM + [("onset.time", 10), ("onset.curve", 0)]),
         ("like4a_w3", "Like 4a, wider x3", "Formants three times as wide during the move",
          DUM + [("onset.bandwidth", 3)])],
        ab_folder="c01_bass",
        extra_clips=[("before", "Phase 4a", "Round 3's best (with the laser)", "before", False,
                      dl.read_wav(HERE / "onsets" / "c01_bass" / "02_phase4a.wav"))],
        extra_questions=[{"id": "doo", "text": "Which ones have the 'doo'?", "multi": True,
                          "choices": [{"id": "none", "label": "None of them"}]}])


def fold(sections, notes):
    return [("range.shift", expand.fit_shift(sections, notes))]


def violin():
    notes = make_ab.melody(12)
    sections = expand.resolve(make_4b.DATA, "strings.violin")
    folded = fold(sections, [n for _, n, _ in notes])
    no_glides = [("phrase.mode", 3)]
    return make_4b3.test(
        "violin", "Violin: folded an octave down (new default)",
        "Violin: is the folded violin clean, and are glides OK now?",
        "Round 3: only the octave-lower violin was clean, and it was the best. High parts now "
        "fold down by default: the whole channel moves down by octaves while its middle note is "
        f"above C5 (this melody: {folded[0][1]:+d} semitones).",
        "strings.violin", notes,
        [("fold", "Folded, legato (new default)", "strings.violin as it now is", folded),
         ("fold_no_glides", "Folded, no glides", "Every note a new onset: sample for sample "
          "round 3's pick", folded + no_glides)],
        ab_folder="c06_violin")


def k525():
    """Round 3's K525 test with the fold; the router's script is at written pitch."""
    data = make_4b.DATA
    violin = expand.resolve(data, "strings.violin")
    script = (make_4b3.BALANCE / "monk_p1ch1.txt").read_text(encoding="utf-8").split()
    notes = [int(script[i + 1]) for i, w in enumerate(script) if w == "on"]
    shift = expand.fit_shift(violin, notes)
    with_shift = lambda s: expand.merge(s, {"range": {"shift": shift}})  # noqa: E731
    singer = expand.merge(expand.resolve(data, "choir.aahs"), {
        "onset": {"attack": 40}, "ending": {"release": 120}, "phrase": {"mode": 0},
        "ensemble": {"unison": 1}, "voice": {"size": 0.5}})
    variants = [
        ("violin", "Violin, folded (legato)", "strings.violin as it now is", with_shift(violin)),
        ("violin_detached", "Violin, folded, no glides", "Every note a new onset",
         with_shift(expand.merge(violin, {"phrase": {"mode": 3}}))),
        ("singer", "Singer, folded", "Round 3's singer on 'ah', folded", with_shift(singer)),
    ]
    return _k525(variants, make_4b3.k525_script, shift)


def _k525(variants, k525_script, shift):
    import numpy as np
    B = make_4b3.BALANCE
    band = dl.read_wav(B / "band.wav")
    full = dl.read_wav(B / "full.wav")
    plain = dl.read_wav(B / "monk_p1ch1.wav")
    rms = make_4b3.rms
    target = rms(full) * 10 ** (-4.5 / 20)
    clips = [("gervill", "Gervill only", "What midis2jam2 plays without Delay Lama", "gervill", True,
              dl.read_wav(B / "ab" / "00_gervill.wav")),
             ("plain_p6", "Your pick (+6 dB)", "Phase 2's monk (plain mode, an octave low), "
              "round 3's best", "plain_p6", False, dl.read_wav(B / "ab" / "02_p6.wav"))]
    for cond, label, desc, sections in variants:
        path = OUT / "scripts" / f"k525_{cond}.txt"
        path.write_text(k525_script(sections), encoding="utf-8")
        monk = dl.render(path, monks=4, tail=0)
        n = min(len(monk), len(band))
        monk = monk[:n] * (rms(plain) / rms(monk[:n])) * 10 ** (6 / 20)
        mix = band[:n] + monk
        mix *= target / rms(mix)
        print(f"k525 {cond}: peak {20 * np.log10(np.abs(mix).max()):.1f} dBFS")
        clips.append((cond, label, desc, cond, False, mix))
    conds = [(c[0], c[1]) for c in clips if not c[4]]
    questions = [
        {"id": "best", "text": "Which works best as violin 1 in the music?", "multi": False,
         "choices": make_4b.choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
        {"id": "glitch", "text": make_4b3.GLITCH, "multi": True,
         "choices": make_4b.choices(conds, [{"id": "none", "label": "None of them"}])},
    ]
    return make_4b.clip_set(
        "k525", "Violin 1 in the music, folded (K525)",
        "Mozart K525, the first 30 s: does the folded monk work as violin 1?",
        f"A choir of 4 monks sings violin 1 in profile mode, folded {shift:+d} semitones by the "
        "new default (D37), as loud as your +6 dB pick.", clips, questions)


def main():
    (OUT / "scripts").mkdir(parents=True, exist_ok=True)
    tests = [bass(), violin(), k525()]
    for t in tests:
        for q in t["questions"]:
            q.pop("fixed", None)
    manifest = {
        "format": 1,
        "title": "Phase 4b round 4: the bass 'doo', and the folded violin",
        "intro": "The bass: which part of phase 4a's settings makes its 'doo', and can it stay "
                 "without the laser? The violin: high parts now sing an octave lower by default "
                 "(your round 3 pick), alone and in K525.",
        "tests": tests,
    }
    (OUT / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("wrote", sum(len(t["clips"]) for t in tests), "clips")


if __name__ == "__main__":
    main()
