"""Phase 2, D34 applied: live playback before and after the balance, at their real levels.

Inputs, from `./gradlew :app:delayLamaBalance` (BalanceRender.kt) with the default balance (6 dB):
band.wav (Gervill without channel 1), full.wav (Gervill, every channel), monk_p1ch1.wav (the helper singing
channel 1) and live.wav (what live playback now sends to the speakers: the band 6 dB down on Gervill's audio line,
plus the monk).

Writes ab/*.wav and listening.json. Unlike ../balance, nothing is loudness-matched: the clips keep the levels
live playback has relative to each other, so the drop in overall loudness is audible too. All three are 3 dB down
(HEADROOM), since 'before' peaked above full scale (+2.3 dBFS, which Windows' mixer limits live). Loudness-matched, live.wav is the +6 dB pick
(../balance/ab/02_p6.wav) to within rounding.

Run: py renders\\phase2\\d34\\make_d34.py
"""
import json
import pathlib

import numpy as np
from scipy.io import wavfile

HERE = pathlib.Path(__file__).resolve().parent
AB = HERE / "ab"
HEADROOM = 10 ** (-3 / 20)


def read(name):
    rate, x = wavfile.read(HERE / name)
    return rate, x.astype(np.float64) / 32768.0


def rms(x):
    return float(np.sqrt((x.mean(axis=1) ** 2).mean()))


def db(v):
    return 20 * np.log10(max(v, 1e-12))


def write(name, x, rate):
    wavfile.write(AB / name, rate, (np.clip(x, -1, 1) * 32767).round().astype(np.int16))


def main():
    AB.mkdir(exist_ok=True)
    rate, full = read("full.wav")
    _, band = read("band.wav")
    _, monk = read("monk_p1ch1.wav")
    _, live = read("live.wav")
    before = band + monk
    write("00_gervill.wav", full * HEADROOM, rate)
    write("01_before.wav", before * HEADROOM, rate)
    write("02_now.wav", live * HEADROOM, rate)
    drop = db(rms(before)) - db(rms(live))
    print(f"RMS: Gervill only {db(rms(full)):.1f}, before {db(rms(before)):.1f}, now {db(rms(live)):.1f} dBFS; "
          f"peaks {db(np.abs(before).max()):.1f} and {db(np.abs(live).max()):.1f} dBFS")

    manifest = {
        "format": 1,
        "title": "Phase 2: the +6 dB balance in live playback (D34)",
        "intro": ("K525's first 30 s with violin 1 sung by Delay Lama (choir of 4, plain mode), as live playback "
                  "sends it to the speakers, at their real relative levels (nothing loudness-matched; all 3 dB "
                  "down for headroom, since 'Before' peaked above full scale). 'Now' turns Gervill's "
                  "audio line down 6 dB while a channel is sung; the monk is unchanged. Loudness-matched, 'Now' "
                  f"is your +6 dB pick. Overall it is {drop:.1f} dB quieter than before."),
        "tests": [{
            "id": "d34_live",
            "title": "Balance in live playback",
            "question": "Is the monk now heard as the lead, the way your +6 dB pick sounded?",
            "notes": "Reference: Gervill alone. Compare 'Before' (phase 2 as you heard it live) with 'Now'.",
            "blind": False,
            "clips": [
                {"file": "ab/00_gervill.wav", "label": "Gervill only", "reference": True,
                 "desc": "What midis2jam2 plays without Delay Lama"},
                {"file": "ab/01_before.wav", "label": "Before", "condition": "before",
                 "desc": "Phase 2 live: band at full level, monk at the helper's default"},
                {"file": "ab/02_now.wav", "label": "Now (D34)", "condition": "now",
                 "desc": "Band 6 dB down on Gervill's line, monk unchanged"},
            ],
            "questions": [
                {"id": "balance", "text": "Is the balance in 'Now' right?", "multi": False,
                 "choices": [{"id": "right", "label": "Yes, like my +6 dB pick"},
                             {"id": "more", "label": "The monk needs more"},
                             {"id": "less", "label": "The monk is too loud"}]},
                {"id": "loudness", "text": f"'Now' is {drop:.1f} dB quieter overall. Is that OK?", "multi": False,
                 "choices": [{"id": "ok", "label": "Fine, I turn my volume up"},
                             {"id": "split", "label": "Too quiet: take some of it from the monk side "
                                                      "(a louder monk, which may clip big chords)"}]},
            ],
        }],
    }
    (HERE / "listening.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
