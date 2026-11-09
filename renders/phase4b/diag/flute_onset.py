"""Flute 'plucked laser': spectrogram of c05's tongued notes, original vs steady vowel."""
import pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dl

R = dl.ROOT / "renders"
OUT = pathlib.Path(__file__).parent / "flute"
OUT.mkdir(exist_ok=True)
orig = dl.render(R / "phase4a/ab/scripts/c05_flute_+0.txt")
steady = dl.render(R / "phase1-fix/scripts/c05_flute_+0_steady_vowel.txt")
# note-on times from the script
t, ons = 0.0, []
for line in (R / "phase4a/ab/scripts/c05_flute_+0.txt").read_text().splitlines():
    if line.startswith("wait "): t += float(line.split()[1]) / 1000
    elif line.startswith("on "): ons.append((round(t, 3), int(line.split()[1])))
print(ons[:8])
for name, x in (("orig", orig), ("steady", steady)):
    t1 = ons[1][0]
    dl.spectrogram_png(x, OUT / f"{name}_n2.png", t1 - 0.04, t1 + 0.16, fmax=5000, win=0.008,
                       title=f"flute {name}, note 2 (helper {ons[1][1]})", marks=[t1, t1 + 0.02])
    # pitch track over the transition
    m = dl.mono(x)
    tt, f0, ap = dl.yin(m, t1 - 0.02, t1 + 0.12, fmin=300, fmax=2500, win=0.012, hop=0.002)
    print(name, "f0 (st rel. note-12):", np.round(dl.hz_to_note(f0) - (ons[1][1] - 12), 2)[::3].tolist())
    for lo, hi in ((600, 1300), (1300, 2600), (2600, 5000)):
        bt, db = dl.band_db(x, t1 - 0.02, t1 + 0.12, lo, hi, win=0.006, hop=0.004)
        print(f"  {lo}-{hi} Hz dB:", np.round(db - db.max(), 0).astype(int).tolist())
