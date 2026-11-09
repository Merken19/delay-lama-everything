"""Phase 4b, round 3 (after the user's answers in renders/phase4b/round2/answers.md).

Round 2: every onset vowel move glitched, darker as well as brighter (bass
small move, trumpet darker onset, guitar 'wa'); steady onsets never did, and
were the best imitation for trumpet, guitar and clean guitar. The profiles
now start steady (D33). The bass lost its 'doo' that way, and the violin
still glitched with every variant.

This round tries the one lever left for consonants, the formants themselves:
Delay Lama's are very narrow (32.5 / 47.5 / 62.5 Hz), so a moving vowel rings
as a pitch. `onset.bandwidth` widens them while the onset vowel moves (with
make-up gain, so the onset is as loud as before), then returns them exactly
to the DSP's own. `onset.after_rest` keeps a vowel move for the first note
after a break (the user's guitar idea). The violin gets more suspects, and
violin 1 of K525 is sung in the band at the user's balance (+6 dB), as a
violin and as a singer.

Run: py renders/phase4b/make_4b3.py  (writes renders/phase4b/round3/)
"""

import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = sys.argv[:1]
import make_4b  # noqa: E402
from make_4b import make_ab, dl, expand  # noqa: E402

OUT = HERE / "round3"
make_4b.HERE = OUT  # clip_set and render write under round3/
ROOT = HERE.parent.parent
BALANCE = ROOT / "renders" / "phase2" / "balance"

GLITCH = ("Which clips have a glitch (laser, high pitch at a start, too high between notes, "
          "whistle, wobble)?")


def test(test_id, title, question, notes_text, profile, notes, variants, ab_folder=None,
         extra_clips=(), extra_questions=(), monks=1):
    clips = []
    if ab_folder:
        clips.append(("gervill", "Gervill", "Reference", "gervill", True,
                      dl.read_wav(make_4b.AB / ab_folder / "01_gervill_solo.wav")))
    clips += list(extra_clips)
    for cond, label, desc, extra in variants:
        x = make_4b.render(f"{test_id}_{cond}", make_4b.script(notes, profile, extra), monks)
        clips.append((cond, label, desc, cond, False, x))
    conds = [(c[0], c[1]) for c in clips if not c[4]]
    questions = [
        {"id": "glitch", "text": GLITCH, "multi": True,
         "choices": make_4b.choices(conds, [{"id": "none", "label": "None of them"}])},
        # Extra questions pick among the clips (plus their own choices), unless fixed.
        *[q if q.get("fixed") else {**q, "choices": make_4b.choices(conds, q["choices"])}
          for q in extra_questions],
        {"id": "best", "text": "Which sounds most like someone imitating the instrument?",
         "multi": False, "choices": make_4b.choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
    ]
    return make_4b.clip_set(test_id, title, question, notes_text, loudness_matched(clips), questions)


def active_rms(x, floor=1e-4):
    """RMS of the samples that sound (rests and tails don't count)."""
    mono = x.mean(axis=1)
    sounding = mono[np.abs(mono) > floor]
    return float(np.sqrt((sounding ** 2).mean())) if len(sounding) else 1.0


def loudness_matched(clips):
    """Every clip at the reference's loudness (Gervill), so the clips differ in
    sound, not in level. Rounds 1 and 2 used one gain per set, which left the
    articulator's bass 16-18 dB under phase 4a's clip."""
    ref = next((c[5] for c in clips if c[4]), clips[0][5])
    target = active_rms(ref)
    return [(*c[:5], c[5] * (target / active_rms(c[5]))) for c in clips]


D_MOVE = [("onset.vowel", 0.55), ("onset.time", 50)]


def bass():
    return test(
        "bass", "Bass: a 'doo' with wider formants",
        "Bass: which keep the 'doo' without the laser?",
        "Round 2: only phase 4a had the 'doo' (with the laser). The 'd' clips move the vowel "
        "from 0.55 to 'u' at each start, like phase 4a; 'wider' widens Delay Lama's formants "
        "during that move (same loudness).",
        "bass.finger", make_ab.bass_line(),
        [("steady", "Steady (new default)", "No onset vowel move", []),
         ("d", "'d', narrow", "The 'd' move with Delay Lama's own formants (the laser, as a check)",
          D_MOVE),
         ("d_w2", "'d', wider x2", "Formants twice as wide during the move", D_MOVE + [("onset.bandwidth", 2)]),
         ("d_w4", "'d', wider x4", "Formants four times as wide during the move",
          D_MOVE + [("onset.bandwidth", 4)]),
         ("d_fast_w4", "Fast 'd', wider x4", "A 25 ms move, as fast as phase 4a's, formants x4",
          [("onset.vowel", 0.55), ("onset.time", 25), ("onset.bandwidth", 4)])],
        ab_folder="c01_bass",
        extra_clips=[("before", "Phase 4a", "Round 2's 'doo-doo' (with the laser)", "before", False,
                      dl.read_wav(HERE / "onsets" / "c01_bass" / "02_phase4a.wav"))],
        extra_questions=[{"id": "doo", "text": "Which ones have the 'doo'?", "multi": True,
                          "choices": [{"id": "none", "label": "None of them"}]}])


def trumpet():
    t = [("onset.vowel", 0.75)]  # the profile's 't': hold the colour 15 ms, then step
    return test(
        "trumpet", "Trumpet: tonguing with wider formants",
        "Trumpet: which sound tongued without a high pitch at the starts?",
        "Round 2: steady onsets were best and glitch-free; a darker onset glitched. These try a "
        "brighter 't' (as phase 4a's) with and without wider formants.",
        "trumpet", make_ab.melody(0),
        [("steady", "Steady (new default)", "Round 2's pick", []),
         ("t", "'t', narrow", "Onset colour 0.75 for 15 ms, then a step to the nucleus (as a check)", t),
         ("t_w3", "'t', wider x3", "The same 't' with formants three times as wide",
          t + [("onset.bandwidth", 3)]),
         ("d_w3", "Soft 'd', wider x3", "Onset 0.75 gliding to the nucleus over 40 ms, formants x3",
          t + [("onset.curve", 3), ("onset.time", 40), ("onset.bandwidth", 3)])],
        ab_folder="c03_trumpet",
        extra_questions=[{"id": "tongued", "text": "Which ones sound tongued (a 't' or 'd' at "
                          "the start of notes)?", "multi": True,
                          "choices": [{"id": "none", "label": "None of them"}]}])


def guitar():
    wa = [("onset.vowel", 0), ("onset.time", 120)]
    return test(
        "guitar", "Overdrive guitar: 'wa' only at the start",
        "Overdrive guitar: does a 'wa' on the first note work?",
        "Round 2: 'wa' on every note glitched and wasn't realistic; you suggested it only where "
        "the guitar starts after a break. This phrase has one start, so 'at the start' means the "
        "first note only.",
        "guitar.overdrive", make_ab.melody(-12),
        [("steady", "Steady (new default)", "Round 2's pick", []),
         ("wa_start", "'wa' at the start, narrow", "The first note only (onset.after_rest 400 ms)",
          wa + [("onset.after_rest", 400)]),
         ("wa_start_w3", "'wa' at the start, wider x3", "First note only, formants x3 during the move",
          wa + [("onset.after_rest", 400), ("onset.bandwidth", 3)]),
         ("wa_all_w3", "'wa' on every note, wider x3", "Round 2's glitchy 'wa', formants x3",
          wa + [("onset.bandwidth", 3)])],
        ab_folder="c07_guitar")


def violin():
    no_glides = [("phrase.mode", 3)]
    return test(
        "violin", "Violin: find the glitch (round 3)",
        "Violin: which clips have a glitch, and what does it sound like?",
        "Round 2: every variant glitched, 'no glides' a little less. The violin sits at F5-E6, "
        "where Delay Lama's pitch moves in whole-sample steps of 30-50 cents, so its vibrato "
        "and glides become small stairs; the octave-lower clip halves those steps. Phase 4a's "
        "violin is here too: you called it 'a tad too bright', not glitchy.",
        "strings.violin", make_ab.melody(12),
        [("now", "Now (legato)", "strings.violin with the new steady onset", []),
         ("no_glides", "No glides", "Every note a new onset (round 2's least glitchy)", no_glides),
         ("straight", "No glides, straight", "No glides and no vibrato beyond Delay Lama's floor",
          no_glides + [("vibrato.depth", 0.2)]),
         ("low", "No glides, octave lower", "No glides, sung an octave below the written part",
          no_glides + [("range.octave", -1)]),
         ("no_breath", "No glides, no breath", "No glides and breath 0 (no high breath partials)",
          no_glides + [("body.breath", 0)]),
         ("quick", "Quick glides", "Legato, but each glide takes ~15 ms instead of ~130 ms",
          [("phrase.glide", 0.05)])],
        ab_folder="c06_violin",
        extra_clips=[("phase4a", "Phase 4a", "The phase 4a A/B violin, as written", "phase4a", False,
                      dl.read_wav(make_4b.AB / "c06_violin" / "02_monk_as_written_solo.wav"))],
        extra_questions=[{"id": "kind", "text": "What does the glitch sound like? (pick all you hear)",
                          "multi": True, "fixed": True, "choices": KIND_CHOICES}])


KIND_CHOICES = [
    {"id": "stairs", "label": "Stepped or wobbly pitch"},
    {"id": "whistle", "label": "Whistle or ringing above the note"},
    {"id": "between", "label": "Wrong or too high between notes"},
    {"id": "start", "label": "Something at the starts of notes"},
    {"id": "click", "label": "Clicks"},
    {"id": "other", "label": "Something else (please note it)"},
]


def k525_script(sections):
    """The router's channel 1 script from the phase 2 balance render, sung in
    profile mode: protocol 1 and the profile first, the rest as recorded."""
    lines = ["hello 1", "set articulator 1"] + expand.set_lines(sections)
    lines += (BALANCE / "monk_p1ch1.txt").read_text(encoding="utf-8").splitlines()
    return "\n".join(lines) + "\n"


def rms(x):
    return float(np.sqrt((x.mean(axis=1) ** 2).mean()))


def k525():
    band = dl.read_wav(BALANCE / "band.wav")
    full = dl.read_wav(BALANCE / "full.wav")
    plain = dl.read_wav(BALANCE / "monk_p1ch1.wav")
    target = rms(full) * 10 ** (-4.5 / 20)  # as make_balance.py
    data = make_4b.DATA
    violin = expand.resolve(data, "strings.violin")
    detached = expand.merge(violin, {"phrase": {"mode": 3}})
    singer = expand.merge(expand.resolve(data, "choir.aahs"), {
        "onset": {"attack": 40}, "ending": {"release": 120}, "phrase": {"mode": 0},
        "ensemble": {"unison": 1}, "voice": {"size": 0.5}})
    variants = [
        ("violin", "Violin (legato)", "strings.violin, steady onset, glides between connected notes",
         violin),
        ("violin_detached", "Violin, no glides", "strings.violin, every note a new onset", detached),
        ("singer", "Singer", "A singer on 'ah' instead of a violin imitation: quick attack, lead "
         "vibrato, glides only on slurs", singer),
    ]
    clips = [("gervill", "Gervill only", "What midis2jam2 plays without Delay Lama", "gervill", True,
              dl.read_wav(BALANCE / "ab" / "00_gervill.wav")),
             ("plain_p6", "Your pick (+6 dB)", "Phase 2's monk (plain mode, an octave low) at "
              "+6 dB, as you picked", "plain_p6", False, dl.read_wav(BALANCE / "ab" / "02_p6.wav"))]
    report = []
    for cond, label, desc, sections in variants:
        text = k525_script(sections)
        (OUT / "scripts" / f"k525_{cond}.txt").write_text(text, encoding="utf-8")
        monk = dl.render(OUT / "scripts" / f"k525_{cond}.txt", monks=4, tail=0)
        n = min(len(monk), len(band))
        monk = monk[:n] * (rms(plain) / rms(monk[:n])) * 10 ** (6 / 20)  # the plain monk's RMS, +6 dB
        mix = band[:n] + monk
        mix *= target / rms(mix)
        report.append(f"k525 {cond}: peak {20 * np.log10(np.abs(mix).max()):.1f} dBFS")
        clips.append((cond, label, desc, cond, False, mix))
    conds = [(c[0], c[1]) for c in clips if not c[4]]
    questions = [
        {"id": "best", "text": "Which works best as violin 1 in the music?", "multi": False,
         "choices": make_4b.choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
        {"id": "glitch", "text": GLITCH, "multi": True,
         "choices": make_4b.choices(conds, [{"id": "none", "label": "None of them"}])},
    ]
    print("\n".join(report))
    # One gain for the set: the mixes are already loudness-matched.
    return make_4b.clip_set(
        "k525", "Violin 1 in the music (K525)",
        "Mozart K525, the first 30 s: does the monk work as violin 1, as a violin or as a singer?",
        "Gervill plays the band; a choir of 4 monks sings violin 1 in profile mode at the written "
        "pitch, as loud as your +6 dB pick. 'Your pick' is the phase 2 clip you chose (plain mode, "
        "an octave low). No glitch fixes beyond the steady onset are in these yet.",
        clips, questions)


def main():
    (OUT / "scripts").mkdir(parents=True, exist_ok=True)
    tests = [bass(), trumpet(), guitar(), violin(), k525()]
    for t in tests:
        for q in t["questions"]:
            q.pop("fixed", None)
    manifest = {
        "format": 1,
        "title": "Phase 4b round 3: wider formants, and violin in the music",
        "intro": "Round 2 showed that any vowel move at a note's start glitches, so every profile "
                 "now starts steady. Delay Lama's formants are very narrow, which is why a moving "
                 "vowel rings like a pitch (the laser). These clips widen the formants only while "
                 "the onset vowel moves, to see whether consonants like 'd', 't' and 'w' can come "
                 "back without the laser. Then more violin suspects, and violin 1 of K525 in the "
                 "band at your +6 dB balance.",
        "tests": tests,
    }
    (OUT / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("wrote", sum(len(t["clips"]) for t in tests), "clips")


if __name__ == "__main__":
    main()
