"""Bass 'laser gun' onset: what reaches the formants grain by grain.

Renders one c01-style bass note (A1, helper note 45, voice 0.35, breath 0.25,
glide 0, vibrato floor) with different onset vowel moves, and reports for each
grain-sized frame the strongest spectral peak (the formant ring that the ear
hears as a pitch when grains barely overlap)."""

import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dl  # noqa: E402

OUT = pathlib.Path(__file__).parent / "bass"
OUT.mkdir(exist_ok=True)

HEAD = """hello 0
bendrange 12
cc 7 127
set echo_amount 0
set glide 0
set vibrato 0
set vibrato_rate 0.5
set voice 0.35
set breath 0.25
set gain 1
"""


def note(note_number, v0, v1, ms, step_ms, level_ms=0, hold=400):
    lines = [HEAD, f"set vowel {v0}"]
    if level_ms:
        lines.append("set gain 0")
    lines.append("wait 100")
    lines.append(f"on {note_number} 100")
    t = 0
    while t < max(ms, level_ms):
        t += step_ms
        x = min(1.0, t / ms) if ms else 1.0
        s = 3 * x * x - 2 * x * x * x  # ease
        lines.append(f"wait {step_ms}")
        lines.append(f"set vowel {v0 + (v1 - v0) * s:.4f}")
        if level_ms:
            lines.append(f"set gain {min(1.0, t / level_ms):.4f}")
    lines.append(f"wait {hold}")
    lines.append(f"off {note_number}")
    lines.append("wait 200")
    return "\n".join(lines) + "\n"


def peaks(x, t0, t1, period):
    """Per period-long frame: frequency of the strongest peak in 250-3500 Hz."""
    m = dl.mono(x)
    n = int(period * dl.SR)
    res = []
    t = t0
    freqs = np.fft.rfftfreq(8192, 1 / dl.SR)
    sel = (freqs > 250) & (freqs < 3500)
    while t < t1:
        a = int(t * dl.SR)
        f = np.abs(np.fft.rfft(m[a:a + n] * np.hanning(n), 8192))
        k = np.argmax(f[sel])
        res.append((round((t - 0.1) * 1000), int(freqs[sel][k])))
        t += period
    return res


CASES = [
    ("steady_0.12", dict(note_number=45, v0=0.12, v1=0.12, ms=0, step_ms=5)),
    ("sweep25_5ms", dict(note_number=45, v0=0.55, v1=0.12, ms=25, step_ms=5)),
    ("sweep25_1ms", dict(note_number=45, v0=0.55, v1=0.12, ms=25, step_ms=1)),
    ("sweep100_1ms", dict(note_number=45, v0=0.55, v1=0.12, ms=100, step_ms=1)),
    ("sweep25_level25", dict(note_number=45, v0=0.55, v1=0.12, ms=25, step_ms=1, level_ms=25)),
    ("A2_sweep25_1ms", dict(note_number=57, v0=0.55, v1=0.12, ms=25, step_ms=1)),
]

if __name__ == "__main__":
    for name, kw in CASES:
        x = dl.render(note(**kw))
        dl.write_wav(OUT / f"{name}.wav", x)
        dl.spectrogram_png(x, OUT / f"{name}.png", 0.09, 0.30, fmax=4000, win=0.006,
                           title=name, marks=[0.1])
        period = 1 / (55 if kw["note_number"] == 45 else 110)
        print(name, peaks(x, 0.1, 0.22, period))
