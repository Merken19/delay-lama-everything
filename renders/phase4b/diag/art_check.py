import pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import dl
H = "hello 1\nset articulator 1\ncc 7 127\nset vibrato.rate 6\n"
x = dl.mono(dl.render(H + "set phrase.mode 1\nset phrase.glide 0.15\non 57 100\nwait 300\non 64 100\nwait 1\noff 57\nwait 400\n", tail=0))
t, f, ap = dl.yin(x, 0.25, 0.68, fmin=150, fmax=600, win=0.025, hop=0.01)
print("legato st rel E4:", np.round(dl.hz_to_note(f) - 64, 2).tolist())
def flare(extra):
    y = dl.mono(dl.render(H + "set voice.size 0.6\nset nucleus.vowel 0.6\nset nucleus.pitch_track 0\nset onset.vowel 0.75\nset body.breath 0.45\n" + extra + "on 76 100\nwait 400\n", tail=0))
    hz = 440 * 2 ** (7 / 12) * 3
    def lv(ms):
        a = int(ms / 1000 * dl.SR); n = 480; s = y[a:a + n] * np.hanning(n)
        return abs(np.sum(s * np.exp(-2j * np.pi * hz * np.arange(n) / dl.SR))) / n
    on = max(lv(m) for m in range(0, 60, 2)); body = max(lv(m) for m in range(200, 380, 10))
    return round(20 * np.log10(on / body), 1)
for name, extra in [("glide25 nomask", "set onset.time 25\nset onset.mask 0\n"),
                    ("glide25 mask", "set onset.time 25\nset onset.mask 1\n"),
                    ("glide60 mask", "set onset.time 60\nset onset.mask 1\n"),
                    ("step15", "set onset.time 15\nset onset.curve 0\nset onset.mask 0\n"),
                    ("step15 attack15", "set onset.time 15\nset onset.curve 0\nset onset.attack 15\n"),
                    ("glide25 attack50", "set onset.time 25\nset onset.attack 50\n"),
                    ("steady", "set onset.vowel -1\n")]:
    print(name, flare(extra))
