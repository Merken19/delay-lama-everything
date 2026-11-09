"""Phase 4b, round 2 (after the user's answers in renders/phase4b/answers.md).

The mask did not remove any glitch; only a steady onset did. Working theory:
an onset vowel brighter than the note's nucleus is heard as a high pitch or a
laser, at any level. This set tries consonants that never go brighter than
the nucleus, and takes the violin and clean guitar demos apart.

Run: py renders/phase4b/make_4b2.py  (writes renders/phase4b/round2/)
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = sys.argv[:1]
import make_4b  # noqa: E402
from make_4b import make_ab, dl  # noqa: E402

OUT = HERE / "round2"
make_4b.HERE = OUT  # clip_set and render write under round2/


def test(test_id, title, question, notes_text, profile, notes, variants, ab_folder=None,
         before=None, monks=1):
    clips = []
    if ab_folder:
        clips.append(("gervill", "Gervill", "Reference", "gervill", True,
                      dl.read_wav(make_4b.AB / ab_folder / "01_gervill_solo.wav")))
    if before:
        clips.append(("before", before[0], before[1], "before", False, dl.read_wav(before[2])))
    for cond, label, desc, extra in variants:
        x = make_4b.render(f"{test_id}_{cond}", make_4b.script(notes, profile, extra), monks)
        clips.append((cond, label, desc, cond, False, x))
    conds = [(c[0], c[1]) for c in clips if not c[4]]
    questions = [
        {"id": "glitch", "text": "Which clips have a glitch (laser, high pitch at a start, too high "
         "between notes, whistle)?", "multi": True,
         "choices": make_4b.choices(conds, [{"id": "none", "label": "None of them"}])},
        {"id": "best", "text": "Which sounds most like someone imitating the instrument?",
         "multi": False, "choices": make_4b.choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
    ]
    return make_4b.clip_set(test_id, title, question, notes_text, clips, questions)


STEADY = [("onset.vowel", -1)]


def main():
    for d in ("scripts",):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    p4b = HERE / "onsets"
    tests = [
        test("bass", "Bass: a 'doo' without the laser",
             "Bass: which keep a 'doo' without the laser?",
             "Round 1: only phase 4a sounded like 'doo-doo', with the laser. These try the "
             "consonant without a bright onset vowel.",
             "bass.finger", make_ab.bass_line(),
             [("steady", "Steady onset", "No onset vowel move (round 1's)", STEADY),
              ("scoop", "Steady + pitch scoop", "No vowel move; the pitch rises 0.7 st into each "
               "note over 40 ms", STEADY + [("onset.scoop", -0.7), ("onset.scoop_time", 40)]),
              ("small", "Small move", "Onset vowel 0.25 to the nucleus over 60 ms (round 1: 0.55)",
               [("onset.vowel", 0.25), ("onset.time", 60), ("onset.mask", 0)]),
              ("lips", "Dark 'b' onset", "Closed-lips onset: vowel 0 with a 5 ms attack "
               "(nothing brighter than the nucleus)", [("onset.vowel", 0), ("onset.time", 40),
                                                      ("onset.attack", 5), ("onset.lips", 1)])],
             ab_folder="c01_bass", before=("Phase 4a", "Heard as 'doo-doo' in round 1",
                                            p4b / "c01_bass" / "02_phase4a.wav")),
        test("trumpet", "Trumpet: tonguing without the high pitch",
             "Trumpet: which have no high pitch at the starts?",
             "Round 1: steady onset was best. These keep it and try a darker tongued start.",
             "trumpet", make_ab.melody(0),
             [("steady", "Steady onset", "Round 1's pick", STEADY),
              ("dark", "Darker onset", "Onset vowel 0.4, below the nucleus (0.6), rising over 40 ms",
               [("onset.vowel", 0.4), ("onset.time", 40), ("onset.curve", 3), ("onset.mask", 0)]),
              ("steady_dip", "Steady, deeper dip", "Steady onset with a deeper re-articulation dip "
               "(level 0.05, 30 ms)", STEADY + [("phrase.dip_level", 0.05), ("phrase.dip_time", 30)])],
             ab_folder="c03_trumpet"),
        test("guitar", "Overdrive guitar: 'nyeow' without going too high",
             "Overdrive guitar: which never go too high between hits?",
             "Round 1: steady onset was 'perfect'. These try a darker 'w' start instead of 'ny'.",
             "guitar.overdrive", make_ab.melody(-12),
             [("steady", "Steady onset", "Round 1's pick", STEADY),
              ("wah", "'wa' onset", "Onset vowel 0 rising to the nucleus over 120 ms (w-a-w)",
               [("onset.vowel", 0), ("onset.time", 120), ("onset.mask", 0)])],
             ab_folder="c07_guitar"),
        test("violin", "Violin: find the glitch",
             "Violin: which clips have a glitch?",
             "The violin demo had a glitch in round 1. Each clip removes one suspect.",
             "strings.violin", make_ab.melody(12),
             [("as_round1", "As in round 1", "strings.violin unchanged", []),
              ("steady", "Steady vowel", "No onset move and no pitch tracking of the vowel",
               STEADY + [("nucleus.pitch_track", 0)]),
              ("detached", "No glides", "Every note a new onset (phrase.mode 3)", [("phrase.mode", 3)]),
              ("drawn", "Drawn glides", "Fixed 60 ms glides through the bend (glide_mode 1)",
               [("phrase.glide_mode", 1)]),
              ("darker", "Darker vowel", "Nucleus 0.8 instead of 'ih' (phase 4a remark)",
               STEADY + [("nucleus.vowel", 0.8), ("nucleus.pitch_track", 0)])],
             ab_folder="c06_violin"),
        test("clean_guitar", "Clean guitar: find the glitch",
             "Clean guitar: which clips have a glitch?",
             "The clean guitar demo had a glitch in round 1. Each clip removes one suspect.",
             "guitar.clean", make_ab.melody(-12),
             [("as_round1", "As in round 1", "guitar.clean unchanged ('d-a-ng')", []),
              ("steady_onset", "Steady onset", "No 'd' onset move", STEADY),
              ("no_ending", "No 'ng' ending", "Steady onset, no closing vowel",
               STEADY + [("ending.vowel", -1)]),
              ("all_steady", "One vowel", "Steady onset, no drift, no ending vowel, no dip vowel",
               STEADY + [("ending.vowel", -1), ("body.vowel", -1), ("phrase.dip_vowel", -1)]),
              ("detached", "Detached", "One vowel and every note a new onset (no dips)",
               STEADY + [("ending.vowel", -1), ("body.vowel", -1), ("phrase.mode", 3)])]),
    ]
    manifest = {
        "format": 1,
        "title": "Phase 4b round 2: consonants without bright onsets",
        "intro": "Round 1 showed the mask does not help: only a steady onset removed the glitches. "
                 "Working theory: an onset vowel brighter than the note's own vowel is heard as a "
                 "high pitch or a laser. These clips try consonants that never go brighter, and "
                 "take the violin and clean guitar demos apart one suspect at a time.",
        "tests": tests,
    }
    (OUT / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("wrote", sum(len(t["clips"]) for t in tests), "clips")


if __name__ == "__main__":
    main()
