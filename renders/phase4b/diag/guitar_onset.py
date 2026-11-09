"""Guitar 'too high between two hits': pitch vs intended, and partial flares, for
the bend-on-time c07 script and copies with one curve removed."""
import pathlib, re, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dl
from trumpet_onset import partial_track, steady
R = dl.ROOT / "renders"
SRC = R / "phase1-fix/scripts/c07_guitar_+0_bend_on_time.txt"
OUT = pathlib.Path(__file__).parent / "guitar"; OUT.mkdir(exist_ok=True)
lines = SRC.read_text().splitlines()
def flat_bend(ls):
    return [l for l in ls if not l.startswith("bend ")]
VARIANTS = {"orig": lines, "steady_vowel": steady(lines, "vowel", 0.5), "no_bend": flat_bend(lines),
            "no_vibrato": steady(lines, "vibrato", 0), "steady_vowel_no_bend": flat_bend(steady(lines, "vowel", 0.5))}
# intended pitch timeline
t, note, bend, ons, timeline = 0.0, None, 8192, [], []
for l in lines:
    w = l.split()
    if not w: continue
    if w[0] == "wait": timeline.append((t, note, bend)); t += float(w[1]) / 1000
    elif w[0] == "on": note = int(w[1]); ons.append((t, note))
    elif w[0] == "bend": bend = int(w[1])
print("notes:", [(round(a, 3), n) for a, n in ons])
def intended(tt):
    best = None
    for a, n, b in timeline:
        if a <= tt: best = (n, b)
    n, b = best
    return n - 12 + (b - 8192) / (8191 if b >= 8192 else 8192) * 12
for name, ls in VARIANTS.items():
    p = OUT / f"{name}.txt"; p.write_text("\n".join(ls) + "\n")
    x = dl.render(p); dl.write_wav(OUT / f"{name}.wav", x); m = dl.mono(x)
    tt, f0, ap = dl.yin(m, ons[0][0] + 0.02, t - 0.05, fmin=150, fmax=1200, win=0.02, hop=0.002)
    dev = dl.hz_to_note(f0) - np.array([intended(a) for a in tt])
    bad = [(round(a, 3), round(d, 2)) for a, d in zip(tt, dev) if abs(d) > 0.6 and abs(abs(d) - 12) > 0.6]
    flares = []
    for t0, n in ons:
        f = 440 * 2 ** ((n - 12 - 69) / 12)
        tr = partial_track(m, t0, f, list(range(0, 150, 5)) + list(range(200, 300, 10)))
        on = max(tr[:30]); body = float(np.median([v for v, h in tr[30:]]))
        flares.append(f"{n}:{on[0]-body:+.0f}(h{on[1]}@{tr[:30].index(on)*5})")
    print(f"{name:22s} pitch off >0.6 st: {len(bad)} frames, first {bad[:6]}")
    print("   flares:", " ".join(flares))
    if name == "orig":
        dl.spectrogram_png(x, OUT / "orig_hits.png", ons[2][0] - 0.05, ons[4][0] + 0.25, fmax=4500, win=0.012,
                           title="guitar orig, notes 3-5", marks=[a for a, n in ons[2:5]])
        print("   pitch dev around note 4 (76 repeat):", [(round(a - ons[3][0], 3), round(d, 2)) for a, d in zip(tt, dev) if -0.06 < a - ons[3][0] < 0.12][::3])
        print("   pitch dev around note 2 (slide):", [(round(a - ons[1][0], 3), round(d, 2)) for a, d in zip(tt, dev) if -0.02 < a - ons[1][0] < 0.12][::3])
