"""Phase 4b, round 6 (after renders/phase4b/round5/answers.md): the bass 'doo'
in the articulator.

Round 5: all three phase 4a basses had the 'doo', including the one with its
vowel held at 'oo' (no vowel move, no glitch, the best). So the 'doo' is
neither generator bug 2 nor the onset move. Measured against that clip
(phase1-fix 03_after_steady_vowel.wav), the articulator's bass.finger had
+5.6 dB at 150-300 Hz and -7 dB at 600-1200 Hz mid-note: a different vowel.
The cause is `nucleus.pitch_track` (default 0.05 per octave from C4): at
A1 it turns 0.12 into about 0.01, so every round 4 'Like 4a' clip sang 'u',
not phase 4a's 'oo'. With the tracking off, nucleus 0.12 and breath 0.25,
the articulator's spectra match phase 4a's within 0.3 dB in every band and
its level envelope matches note for note, except at the 8 note joins where
phase 4a's generator bug leaves no gap (the round 5 'bug fixed' clip, which
has gaps, kept the 'doo').

Run: py renders/phase4b/make_4b6.py  (writes renders/phase4b/round6/)
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.argv = sys.argv[:1]
import make_4b  # noqa: E402
import make_4b3  # noqa: E402
from make_4b import make_ab, dl  # noqa: E402

OUT = HERE / "round6"
make_4b.HERE = OUT  # clip_set and render write under round6/
make_4b3.OUT = OUT
FIX = HERE.parent / "phase1-fix" / "c01_bass"

OO = [("nucleus.pitch_track", 0), ("nucleus.vowel", 0.12)]
COPY = OO + [("body.breath", 0.25), ("onset.attack", 0), ("ending.vowel", -1)]


def bass():
    return make_4b3.test(
        "bass", "Bass: the 'doo' in the articulator",
        "Bass: which have the 'doo'?",
        "Round 5: the 'doo' was in every phase 4a bass, even with no vowel move, so it is the "
        "vowel itself. The articulator lowered it: its vowel tracking turned phase 4a's 'oo' "
        "into a 'u' on low notes. 'Copy of 4a' matches phase 4a's clip in the measurements; "
        "'Held oo' changes only the vowel and keeps the profile's breath, attack and 'm' "
        "ending. Every clip at the same loudness; blind mode is worth it.",
        "bass.finger", make_ab.bass_line(),
        [("steady", "Articulator now", "bass.finger as it is ('u' on low notes)", []),
         ("oo", "Held 'oo'", "Nucleus 0.12 with no vowel tracking; the rest as now", OO),
         ("copy", "Copy of 4a", "Also breath 0.25, crisp attack, no 'm' ending", COPY)],
        ab_folder="c01_bass",
        extra_clips=[("no_move", "Phase 4a, no vowel move", "Round 5's best", "no_move", False,
                      dl.read_wav(FIX / "03_after_steady_vowel.wav"))],
        extra_questions=[{"id": "doo", "text": "Which ones have the 'doo'?", "multi": True,
                          "choices": [{"id": "none", "label": "None of them"}]}])


def main():
    (OUT / "scripts").mkdir(parents=True, exist_ok=True)
    tests = [bass()]
    manifest = {
        "format": 1,
        "title": "Phase 4b round 6: the bass 'doo' in the articulator",
        "intro": "The 'doo' turned out to be phase 4a's 'oo' vowel, which the articulator's "
                 "vowel tracking made darker on low notes. Does the articulator have it now?",
        "tests": tests,
    }
    (OUT / "listening.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("wrote", sum(len(t["clips"]) for t in tests), "clips")


if __name__ == "__main__":
    main()
