import pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dl
x = dl.mono(dl.read_wav(pathlib.Path(__file__).parent / "transition" / sys.argv[1]))
t1 = float(sys.argv[2]); note = int(sys.argv[3]) - 12
f0 = 440 * 2 ** ((note - 69) / 12)
n = int(0.004 * dl.SR)
for ms in range(-8, 90, 4):
    a = int((t1 + ms / 1000) * dl.SR)
    seg = x[a:a + n] * np.hanning(n)
    F = np.fft.rfft(seg, 1 << 15); fr = np.fft.rfftfreq(1 << 15, 1 / dl.SR)
    amps = []
    for h in (0.5, 1, 1.5, 2, 3, 4):
        k = np.argmin(abs(fr - h * f0)); amps.append(20 * np.log10(np.abs(F[k - 3:k + 4]).max() + 1e-9))
    print(f"{ms:4d} ms", " ".join(f"{h}f0:{v:6.1f}" for h, v in zip((0.5, 1, 1.5, 2, 3, 4), amps)))
