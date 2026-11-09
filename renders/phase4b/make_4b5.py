"""Phase 4b, round 5 (after renders/phase4b/round4/answers.md): is phase 4a's
bass 'doo' the generator bug?

Round 4: every articulator copy of phase 4a's DUM settings had the laser and
no 'doo'; only the phase 4a clip had the 'doo'. That clip (phase1-fix
'After') renders the original phase 4a script, which still has generator bug
2 (IMITATION.md 16): 8 of 21 notes start on the previous note's closing 'u'
at a low level and jump 5 ms later, a 'u-e-u' chirp. The same bass from the
fixed generator, and the original with its vowel held at 'oo', were rendered
for the phase 1 fix A/B and are reused here, at Gervill's loudness. Nothing
is rendered.

Run: py renders/phase4b/make_4b5.py  (writes renders/phase4b/round5/)
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = sys.argv[:1]
import make_4b  # noqa: E402
import make_4b3  # noqa: E402
from make_4b import dl  # noqa: E402

OUT = HERE / "round5"
make_4b.HERE = OUT
FIX = HERE.parent / "phase1-fix" / "c01_bass"


def bass():
    clips = [
        ("gervill", "Gervill", "Reference", "gervill", True,
         dl.read_wav(make_4b.AB / "c01_bass" / "01_gervill_solo.wav")),
        ("as_heard", "Phase 4a as heard", "The clip you picked in rounds 3 and 4 (generator bug: "
         "some notes start on the last note's 'u' and jump)", "as_heard", False,
         dl.read_wav(FIX / "02_after.wav")),
        ("fixed", "Phase 4a, bug fixed", "The same bass from the fixed generator: every note "
         "starts on its own 0.55 -> 'oo' move", "fixed", False,
         dl.read_wav(FIX / "05_fixed_generator_after.wav")),
        ("no_move", "Phase 4a, no vowel move", "The original script with the vowel held at 'oo' "
         "(the bug's level jumps stay)", "no_move", False,
         dl.read_wav(FIX / "03_after_steady_vowel.wav")),
    ]
    conds = [(c[0], c[1]) for c in clips if not c[4]]
    pick = lambda: make_4b.choices(conds, [{"id": "none", "label": "None of them"}])  # noqa: E731
    questions = [
        {"id": "doo", "text": "Which ones have the 'doo'?", "multi": True, "choices": pick()},
        {"id": "glitch", "text": make_4b3.GLITCH, "multi": True, "choices": pick()},
        {"id": "best", "text": "Which sounds most like someone imitating the instrument?",
         "multi": False,
         "choices": make_4b.choices(conds, [{"id": "cant_tell", "label": "Can't tell"}])},
    ]
    return make_4b.clip_set(
        "bass", "Bass: is the 'doo' the generator bug?",
        "Bass: which have the 'doo'?",
        "Three phase 4a renders of the same bass line, at the same loudness. Blind mode is "
        "worth it here: 'Phase 4a as heard' has been the pick in every round.",
        make_4b3.loudness_matched(clips), questions)


def main():
    OUT.mkdir(exist_ok=True)
    tests = [bass()]
    manifest = {
        "format": 1,
        "title": "Phase 4b round 5: where the bass 'doo' comes from",
        "intro": "No articulator copy of phase 4a's settings had the 'doo'. The phase 4a clip "
                 "still has a generator bug at some note starts; this checks whether that bug "
                 "is the 'doo'.",
        "tests": tests,
    }
    (OUT / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("wrote", sum(len(t["clips"]) for t in tests), "clips")


if __name__ == "__main__":
    main()
