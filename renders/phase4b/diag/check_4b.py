import pathlib, sys
import numpy as np
H = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(H), str(H.parents[1] / "phase4a" / "ab")]
sys.dont_write_bytecode = True
import dl, make_ab
def flare(m, t0, f0):
    n = int(0.010 * dl.SR); fr = np.fft.rfftfreq(1 << 14, 1 / dl.SR); out = []
    for ms in list(range(0, 80, 5)) + list(range(150, 260, 10)):
        a = int((t0 + ms / 1000) * dl.SR)
        F = np.abs(np.fft.rfft(m[a:a + n] * np.hanning(n), 1 << 14))
        best = max(20 * np.log10(F[np.argmin(abs(fr - h * f0)) - 4:np.argmin(abs(fr - h * f0)) + 5].max() + 1e-9)
                   for h in range(int(1500 // f0) + 1, int(6000 // f0) + 1))
        out.append(best)
    return max(out[:16]) - np.median(out[16:])
for test, notes in (("c03_trumpet", make_ab.melody(0)), ("c07_guitar", make_ab.melody(-12)), ("c05_flute", make_ab.melody(12))):
    for clip in ("02_phase4a", "03_mask0", "04_mask2", "05_steady"):
        m = dl.mono(dl.read_wav(H.parent / "onsets" / test / f"{clip}.wav"))
        fl = [flare(m, t / 1000, 440 * 2 ** ((n - 69) / 12)) for t, n, d in notes if d > 250]
        print(f"{test} {clip:11s} worst {max(fl):+5.1f} dB, notes over +8 dB: {sum(f > 8 for f in fl)}/{len(fl)}")
