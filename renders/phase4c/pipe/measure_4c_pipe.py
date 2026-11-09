"""Phase 4c pipe family: measurements before the ear check (IMITATION.md 16,
c05's flute: "not like a flute at all, more like a plucked laser gun").
Writes measure/measurements.md.

1. Fold: how far D37 moves each phrase (the router's range.shift).
2. Harmonics: each sounding note C4-C7 held 1.5 s on the flute profile (no
   onset burst, vibrato floor only), its first six harmonics against the
   fundamental, next to Gervill's flute at the same pitch. A flute is close
   to a sine; Delay Lama's narrow formants can make one upper harmonic the
   loudest (a whistle at the wrong pitch).
3. Onsets: each note of melody.mid as the router sings it, against its own
   steady state: the loudest 10 ms frame of the first 80 ms (level), the
   largest rise of any harmonic up to 3.5 kHz (flare), and the breath band
   3.5-6 kHz (the burst), for the profile now and without the 'h' burst.
4. Pitch: YIN over each note's first 120 ms, the largest distance from the
   written (sounding) pitch once the note is 15 ms old.
5. Level: the profile's monk against Gervill's flute on melody.mid.
6. Formants: voice.formant3 off (and breath, size, F2) against Gervill.

Run: py renders/phase4c/pipe/measure_4c_pipe.py
"""

import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import pipe_phrases as fp  # noqa: E402
from pipe_phrases import dl, pp  # noqa: E402

sys.path.insert(0, str(HERE.parent / "piano"))
from make_4c_piano import lufs  # noqa: E402

SR = dl.SR
OUT = HERE / "measure"
TMP = HERE / "tmp"
NAMES = "C C# D D# E F F# G G# A A# B".split()


def name(n):
    return f"{NAMES[n % 12]}{n // 12 - 1}"


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def harmonic_db(x, f0, t0, t1, kmax=6):
    seg = dl.mono(x)[int(t0 * SR):int(t1 * SR)]
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    freqs = np.fft.rfftfreq(len(seg), 1 / SR)
    out = []
    for k in range(1, kmax + 1):
        band = np.abs(freqs - k * f0) < 0.025 * k * f0 + 3
        out.append(20 * np.log10(spec[band].max() + 1e-12) if band.any() and k * f0 < SR / 2 else -200)
    return np.array(out)


def gervill_note(note):
    path = TMP / f"g_{note}.mid"
    pp.write_mid(path, {0: (fp.FLUTE_PROGRAM, [(fp.START, note, 1500.0, 90)], [])})
    return pp.gervill(path, TMP / f"g_{note}.wav")


def held(note, extra=()):
    sections = fp.profile(onset={"burst": None, "burst_time": 0}, vibrato={"depth": 0.2})
    phrase = pp.Phrase("one", [(fp.START, note, 1500.0, 90)])
    return dl.render(fp.script(phrase, sections, extra, shift=0), monks=1, tail=100)


def bright_db(x, t0, t1):
    seg = dl.mono(x)[int(t0 * SR):int(t1 * SR)]
    s = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    return 10 * np.log10(s[f > 1500].sum() / s.sum())


def formants(report):
    """voice.formant3 (DSP addition this round) and breath against Gervill."""
    options = {"now": [], "F3 off": [("voice.formant3", 0)],
               "F3 off, breath 0.3": [("voice.formant3", 0), ("body.breath", 0.3)],
               "F3 off, size 0.5": [("voice.formant3", 0), ("voice.size", 0.5)],
               "F3 and F2 off": [("voice.formant3", 0), ("voice.formant2", 0)]}
    report += ["## 6. Taming the buzz: formants and breath", "",
               "Held notes as in section 2: energy above 1.5 kHz in dB of the total (a flute "
               "is mostly below), and the loudest of H2-H4 against H1. F2 off leaves the breath "
               "partials (3.8, 4.95 kHz) on their own, so the share goes up again.", "",
               "| Sounding | Gervill | " + " | ".join(options) + " |",
               "| --- | --- |" + " --- |" * len(options)]
    for note in (64, 69, 72, 76, 81, 84, 87, 90, 93, 96):
        f0 = hz(note)
        cells = []
        for x in [gervill_note(note)] + [held(note, e) for e in options.values()]:
            h = harmonic_db(x, f0, 1.0, 1.9, kmax=4)
            cells.append(f"{bright_db(x, 1.0, 1.9):+.0f} / {max(v - h[0] for v in h[1:] if v > -150):+.0f}")
        report.append(f"| {name(note)} | " + " | ".join(cells) + " |")
    report.append("")


def harmonics(report):
    report += ["## 2. Harmonics of a held note", "",
               "Each sounding note held 1.5 s (no burst, vibrato floor), 0.5-1.4 s after the "
               "onset: harmonics 2-6 in dB against the fundamental (H1), and which harmonic is "
               "the loudest. Gervill's flute (GM 74) at the same note for comparison. '-' is "
               "above 24 kHz.", "",
               "| Note | Monk H2..H6 vs H1 (dB) | Monk loudest | Gervill H2..H6 vs H1 (dB) | Gervill loudest |",
               "| --- | --- | --- | --- | --- |"]
    for note in range(60, 97, 3):
        f0 = hz(note)
        m = harmonic_db(held(note), f0, 1.0, 1.9)
        g = harmonic_db(gervill_note(note), f0, 1.0, 1.9)
        fmt = lambda h: " ".join("-" if v < -150 else f"{v - h[0]:+.0f}" for v in h[1:])
        report.append(f"| {name(note)} | {fmt(m)} | H{1 + int(np.argmax(m))} | {fmt(g)} | "
                      f"H{1 + int(np.argmax(g))} |")
    report.append("")


def stft(x, t0, t1, win=0.010, hop=0.002):
    mono = dl.mono(x)
    n = int(win * SR)
    frames = [np.abs(np.fft.rfft(mono[a:a + n] * np.hanning(n), 4096))
              for a in range(max(0, int(t0 * SR)), int(t1 * SR) - n, int(hop * SR))]
    return 20 * np.log10(np.array(frames) + 1e-12), np.fft.rfftfreq(4096, 1 / SR)


def onsets(report, phrase, variants):
    shift = fp.shift_of(phrase)
    report += [f"## 3. Onsets in {phrase.name}.mid (sung {shift:+d} st)", "",
               "For each note: the first 80 ms against the same note 150-250 ms in (or its "
               "last 100 ms if shorter). Level: loudest 10 ms frame, dB. Flare: the largest "
               "rise of any bin up to 3.5 kHz within 40 dB of the note's loudest. Breath: "
               "3.5-6 kHz band energy. Medians and worst cases over the notes; 'onset' notes "
               "start from silence or a tongued break, 'slur' notes are legato.", "",
               "| Variant | Level med / max | Flare med / max (worst note) | Breath med / max |",
               "| --- | --- | --- | --- |"]
    for label, extra in variants:
        x = dl.render(fp.script(phrase, fp.profile(), extra), monks=1, tail=300)
        lev, flare, breath = [], [], []
        for t, n, d, _ in phrase.notes:
            t0 = t / 1000
            dur = min(d, 600) / 1000
            if dur < 0.12:
                continue
            on, freqs = stft(x, t0, t0 + 0.08)
            ref = stft(x, t0 + min(0.15, dur - 0.1), t0 + min(0.25, dur))[0]
            low = freqs <= 3500
            hi = (freqs > 3500) & (freqs <= 6000)
            tot = lambda s, m: 10 * np.log10((10 ** (s[:, m] / 10)).sum(axis=1))
            lev.append(tot(on, low).max() - tot(ref, low).mean())
            body = ref[:, low].max(axis=0)
            live = body > body.max() - 40
            flare.append(((on[:, low].max(axis=0) - body)[live].max(), n))
            breath.append(tot(on, hi).max() - tot(ref, hi).mean())
        f = [v for v, _ in flare]
        worst = max(flare)
        report.append(f"| {label} | {np.median(lev):+.1f} / {max(lev):+.1f} | {np.median(f):+.1f} / "
                      f"{worst[0]:+.1f} ({name(worst[1] + shift)}) | {np.median(breath):+.1f} / "
                      f"{max(breath):+.1f} |")
    report.append("")


def pitch(report, phrase):
    shift = fp.shift_of(phrase)
    x = dl.render(fp.script(phrase, fp.profile()), monks=1, tail=300)
    report += [f"## 4. Pitch at the onsets of {phrase.name}.mid", "",
               "YIN over each note's first 120 ms after it is 15 ms old: the largest distance "
               "from the sounding pitch (cents), and the median.", ""]
    worst = []
    for t, n, d, _ in phrase.notes:
        t0 = t / 1000
        times, f0s, ap = dl.yin(dl.mono(x), t0 + 0.015, t0 + min(0.12, d / 1000), fmax=2500)
        good = (ap < 0.3) & (f0s > 0)
        if not good.any():
            continue
        c = 1200 * np.log2(f0s[good] / hz(n + shift))
        worst.append((np.abs(c).max(), np.median(c), n + shift))
    w = max(worst)
    report += [f"Worst {w[0]:.0f} cents ({name(w[2])}); medians {min(v[1] for v in worst):+.0f}.."
               f"{max(v[1] for v in worst):+.0f} cents over {len(worst)} notes.", ""]


def level(report):
    phrase = fp.melody()
    g = pp.gervill(HERE / "midi" / "melody.mid", TMP / "melody.wav")
    m = dl.render(fp.script(phrase, fp.profile()), monks=1, tail=300)
    report += ["## 5. Level", "",
               f"melody.mid: Gervill's flute {lufs(g):.1f} LUFS, the profile's monk {lufs(m):.1f} "
               f"LUFS ({lufs(m) - lufs(g):+.1f} dB).", ""]


def main():
    OUT.mkdir(exist_ok=True)
    TMP.mkdir(exist_ok=True)
    fp.write_all_midi()
    report = ["# Phase 4c pipe: measurements", "",
              "Written by `measure_4c_pipe.py` (DelayLamaVoice in profile mode, 48 kHz; Gervill "
              "with the JDK's soundbank).", "", "## 1. Fold (D37)", "",
              "| Phrase | Written median | range.shift |", "| --- | --- | --- |"]
    for p in (fp.tongued(), fp.slurred(), fp.run(), fp.long_notes(), fp.low(), fp.melody()):
        ns = sorted(n for _, n, _, _ in p.notes)
        report.append(f"| {p.name} | {name(ns[len(ns) // 2])} | {fp.shift_of(p):+d} |")
    report.append("")
    harmonics(report)
    onsets(report, fp.melody(), [("now", []), ("no burst", [("onset.burst", -1)]),
                                 ("F3 off", [("voice.formant3", 0)])])
    pitch(report, fp.melody())
    level(report)
    formants(report)
    (OUT / "measurements.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
