"""Listening set: K525's violin 1 sung through midis2jam2's router in profile mode.

The renders come from the real router (midis2jam2 branch `delay-lama`), one
folder per configuration, made with

  .\\gradlew.bat :app:delayLamaBalance "-PdelayLamaBalance=<k525_mvt1.mid>;<this folder>\\<name>;channels=1;<setting>;30"

  auto     profile=auto (the default): program 48 maps to strings.ensemble
  singer   profile=lead.singer: the round 4 pick (D39), now as the router sends it
  plain    profile=plain: phase 2's monk, sample for sample the D34 render

Each folder's live.wav is what live playback sends to the speakers (the band
6 dB down, D36, plus the monks at their own level). They are not
loudness-matched on purpose: the monks of all three modes measure within
0.5 dB of each other, so the D34 balance can be judged as it is.
Run from the top folder: py renders\\phase4b\\router\\make_router.py
"""

import json
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent

GLITCH = ("Which clips have a glitch (laser, high pitch at a start, too high between notes, "
          "whistle, wobble)?")


def main():
    clips_dir = HERE / "clips"
    clips_dir.mkdir(exist_ok=True)
    sources = [
        ("gervill", "Gervill only", "What midis2jam2 plays without Delay Lama", "plain/full.wav", True),
        ("plain", "Plain (phase 2)", "Plain Delay Lama, as you confirmed the balance on (D34)",
         "plain/live.wav", False),
        ("auto", "Auto: string ensemble", "The default: K525's violin 1 is program 48, which maps "
         "to strings.ensemble (slow attack, legato, 4 unison voices), folded an octave",
         "auto/live.wav", False),
        ("singer", "Singer", "lead.singer, your round 4 pick, as the router now sends it "
         "(with note lengths), folded an octave", "singer/live.wav", False),
        ("round4", "Round 4's singer", "The clip you picked in round 4 (made without the "
         "router, loudness-matched)", "../round4/k525/05_singer.wav", False),
    ]
    clips = []
    for i, (cond, label, desc, src, ref) in enumerate(sources, 1):
        name = f"{i:02d}_{cond}.wav"
        shutil.copyfile(HERE / src, clips_dir / name)
        clip = {"file": f"clips/{name}", "label": label, "desc": desc, "condition": cond}
        if ref:
            clip["reference"] = True
        clips.append(clip)

    def choices(conds, extra):
        return [{"id": c, "label": next(x["label"] for x in clips if x["condition"] == c),
                 "condition": c} for c in conds] + extra

    sung = ["plain", "auto", "singer", "round4"]
    manifest = {
        "format": 1,
        "title": "Profile mode in midis2jam2: K525 through the router",
        "intro": "midis2jam2 now sings Delay Lama channels in profile mode by default: each "
                 "channel gets the imitation profile of its program, high parts fold down by "
                 "octaves (D37), and every note carries its length. These are the router's own "
                 "renders of K525's first 30 s with violin 1 sung.",
        "tests": [{
            "id": "k525",
            "title": "K525 violin 1, live mix",
            "question": "Which profile should K525's violin 1 get, and does the balance hold?",
            "notes": "Clips 2-4 are the live mix at real levels (the band 6 dB down); the monks "
                     "of all three measure within 0.5 dB. Clip 5 is round 4's pick for "
                     "comparison (made another way, loudness-matched).",
            "clips": clips,
            "questions": [
                {"id": "best", "text": "Which works best as violin 1 in the music?", "multi": False,
                 "choices": choices(sung, [{"id": "cant_tell", "label": "Can't tell"}])},
                {"id": "glitch", "text": GLITCH, "multi": True,
                 "choices": choices(sung, [{"id": "none", "label": "None of them"}])},
                {"id": "same", "text": "Does 'Singer' sound like round 4's singer?", "multi": False,
                 "choices": [{"id": "same", "label": "The same"},
                             {"id": "singer_better", "label": "Different, the router's is better"},
                             {"id": "round4_better", "label": "Different, round 4's is better"},
                             {"id": "cant_tell", "label": "Can't tell"}]},
                {"id": "balance", "text": "Against the band, are the profile monks (Auto, Singer) "
                 "as easy to hear as the plain one?", "multi": False,
                 "choices": [{"id": "same", "label": "About the same"},
                             {"id": "quieter", "label": "Harder to hear"},
                             {"id": "louder", "label": "Too loud"}]},
            ],
        }],
    }
    (HERE / "listening.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"Wrote {len(clips)} clips and listening.json to {HERE}")


if __name__ == "__main__":
    main()
