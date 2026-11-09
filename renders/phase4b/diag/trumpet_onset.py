"""Trumpet 'high pitch at the start': per note, the strongest partial above
1.5 kHz in the first 80 ms vs the note's body, for the c03 script and copies
with one onset curve removed."""
import pathlib, re, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dl
R = dl.ROOT / "renders"
SRC = R / "phase4a/ab/scripts/c03_trumpet_+0.txt"
OUT = pathlib.Path(__file__).parent / "trumpet"; OUT.mkdir(exist_ok=True)
lines = SRC.read_text().splitlines()

def steady(ls, key, value):
    return [f"set {key} {value}" if re.match(rf"set {key} ", l) else l for l in ls]
def nobend(ls):
    return [l for l in ls if not l.startswith("bend ")]
def nopeak(ls):
    return [re.sub(r"set gain (1\.\d+)", "set gain 1", l) for l in ls]
VARIANTS = {
    "orig": lines,
    "steady_vowel": steady(lines, "vowel", 0.6),
    "no_scoop": nobend(lines),
    "steady_breath": steady(lines, "breath", 0.45),
    "no_peak": nopeak(lines),
    "all_steady": nopeak(nobend(steady(steady(lines, "vowel", 0.6), "breath", 0.45))),
}
t, ons = 0.0, []
for l in lines:
    if l.startswith("wait "): t += float(l.split()[1]) / 1000
    elif l.startswith("on "): ons.append((t, int(l.split()[1])))

def partial_track(m, t0, f0, ms_list):
    """dB of the strongest harmonic above 1.5 kHz, and which harmonic, per 5 ms frame."""
    n = int(0.010 * dl.SR); out = []
    for ms in ms_list:
        a = int((t0 + ms / 1000) * dl.SR)
        F = np.abs(np.fft.rfft(m[a:a + n] * np.hanning(n), 1 << 14)); fr = np.fft.rfftfreq(1 << 14, 1 / dl.SR)
        best = (-200, 0)
        for h in range(int(1500 // f0) + 1, int(6000 // f0) + 1):
            k = np.argmin(abs(fr - h * f0)); v = 20 * np.log10(F[k - 4:k + 5].max() + 1e-9)
            best = max(best, (v, h))
        tot = 20 * np.log10(np.sqrt(np.sum(F ** 2)) + 1e-9)
        out.append((best[0] - tot, best[1]))
    return out

results = {}
for name, ls in VARIANTS.items():
    p = OUT / f"{name}.txt"; p.write_text("\n".join(ls) + "\n")
    x = dl.render(p); dl.write_wav(OUT / f"{name}.wav", x); m = dl.mono(x)
    row = []
    for t0, note in ons:
        f0 = 440 * 2 ** ((note - 12 - 69) / 12)
        tr = partial_track(m, t0, f0, list(range(0, 80, 5)) + list(range(150, 260, 10)))
        onset = max(tr[:16]); body = float(np.median([v for v, h in tr[16:]]))
        row.append((note, round(onset[0] - body, 1), onset[1], tr[:16].index(onset) * 5))
    results[name] = row
    print(f"{name:14s}", " ".join(f"{n}:{d:+.0f}" for n, d, h, ms in row))
print("orig detail (note, excess dB, harmonic, ms):", results["orig"])
