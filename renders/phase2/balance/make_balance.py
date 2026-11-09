"""Phase 2 balance A/B: the Delay Lama monk against the Gervill band (DECISIONS O10).

Inputs (from `./gradlew :app:delayLamaBalance`, see the Kotlin tool BalanceRender.kt):
band.wav (Gervill without channel 1), full.wav (Gervill, every channel),
monk_p1ch1.txt / .wav (the router's script for channel 1, rendered by DelayLamaVoice).

Writes ab/*.wav and listening.json. Every mix is scaled to the same overall RMS as
full.wav, so the clips differ in balance, not in loudness (4.5 dB below full.wav, for headroom); a louder monk therefore
means a quieter band, which is also what live playback would need, since the band
alone already peaks at -0.1 dBFS.

Run: py renders\\phase2\\balance\\make_balance.py
"""
import json
import pathlib
import re
import subprocess

import numpy as np
from scipy.io import wavfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXE = ROOT / "external/delalalalay-lama/Windows/build/Release/DelayLamaVoice.exe"
AB = HERE / "ab"


def read(name):
    rate, x = wavfile.read(HERE / name)
    return rate, x.astype(np.float64) / 32768.0


def rms(x):
    return float(np.sqrt((x.mean(axis=1) ** 2).mean()))


def db(v):
    return 20 * np.log10(max(v, 1e-12))


def write(name, x, rate):
    peak = np.abs(x).max()
    wavfile.write(AB / name, rate, (np.clip(x, -1, 1) * 32767).astype(np.int16))
    return db(peak)


def render_octave_up():
    """The router's script with every note an octave up: the written pitch, since plain mode sings an octave low."""
    src = (HERE / "monk_p1ch1.txt").read_text()

    def up(m):
        return f"{m.group(1)} {min(int(m.group(2)) + 12, 126)}"

    (HERE / "monk_p1ch1_up.txt").write_text(re.sub(r"^(on|off) (\d+)", up, src, flags=re.M))
    subprocess.run([str(EXE), "--render", str(HERE / "monk_p1ch1_up.txt"), str(HERE / "monk_p1ch1_up.wav"),
                    "--monks", "4", "--tail", "0"], check=True, cwd=EXE.parent)


def main():
    AB.mkdir(exist_ok=True)
    render_octave_up()
    rate, full = read("full.wav")
    _, band = read("band.wav")
    _, monk = read("monk_p1ch1.wav")
    _, monk_up = read("monk_p1ch1_up.wav")
    target = rms(full) * 10 ** (-4.5 / 20)  # headroom: the mixes peak up to ~4 dB above full.wav

    clips = [{"file": "ab/00_gervill.wav", "label": "Gervill only", "reference": True,
              "desc": "What midis2jam2 plays without Delay Lama (violin 1 on Gervill)"}]
    write("00_gervill.wav", full * target / rms(full), rate)
    report = []
    variants = [("01_now", monk, 0, "As now (+0 dB)", "What you heard: the monk at the helper's default level, an octave low"),
                ("02_p6", monk, 6, "+6 dB", "Monk 6 dB louder against the band, an octave low"),
                ("03_p12", monk, 12, "+12 dB", "Monk 12 dB louder, an octave low"),
                ("04_p18", monk, 18, "+18 dB", "Monk 18 dB louder, an octave low"),
                ("05_up_now", monk_up, 0, "Octave up, +0 dB", "As now, but singing the written pitch"),
                ("06_up_p6", monk_up, 6, "Octave up, +6 dB", "Written pitch, 6 dB louder"),
                ("07_up_p12", monk_up, 12, "Octave up, +12 dB", "Written pitch, 12 dB louder")]
    for name, voice, gain_db, label, desc in variants:
        mix = band + voice * 10 ** (gain_db / 20)
        mix *= target / rms(mix)
        peak = write(f"{name}.wav", mix, rate)
        band_db = db(rms(band * target / rms(band + voice * 10 ** (gain_db / 20)))) - db(rms(band))
        report.append(f"{name}: band {band_db:+.1f} dB, peak {peak:.1f} dBFS")
        clips.append({"file": f"ab/{name}.wav", "label": label, "desc": desc, "condition": name})

    manifest = {
        "format": 1,
        "title": "Phase 2: monk vs. band balance (Mozart K525, violin 1 sung)",
        "intro": ("The first 30 s of Eine kleine Nachtmusik, i, rendered offline the way phase 2 plays it: Gervill "
                  "plays the band without channel 1, a Delay Lama helper sings channel 1 (choir of 4, plain mode). "
                  "Every mix has the same overall loudness, so a louder monk means a quieter band. Plain mode sings "
                  "an octave below the written part; the 'octave up' clips sing the written pitch."),
        "tests": [{
            "id": "balance_k525",
            "title": "Monk level in the band",
            "question": "Which balance lets you hear the monk as the lead without it sticking out?",
            "notes": "The reference is Gervill alone. Listen for the monk against the violas and cello.",
            "blind": False,
            "clips": clips,
            "questions": [
                {"id": "balance", "text": "Which balance is best?", "multi": False,
                 "choices": [{"id": c["condition"], "label": c["label"], "condition": c["condition"]}
                             for c in clips[1:]] + [{"id": "none", "label": "None: louder still"}]},
                {"id": "octave", "text": "Is the octave part of the problem?", "multi": False,
                 "choices": [{"id": "yes", "label": "Yes, the written pitch is much easier to hear"},
                             {"id": "some", "label": "A little"},
                             {"id": "no", "label": "No, only the level matters"}]},
            ],
        }],
    }
    (HERE / "listening.json").write_text(json.dumps(manifest, indent=2))
    print(f"full rms {db(target):.1f} dB; band {db(rms(band)):.1f}; monk {db(rms(monk)):.1f}; "
          f"monk up {db(rms(monk_up)):.1f}")
    print("\n".join(report))


if __name__ == "__main__":
    main()
