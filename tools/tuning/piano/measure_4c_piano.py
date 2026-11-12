"""Piano: measurements before the ear check (IMITATION.md 16, c02's
"broken detune piano"). Writes measure/measurements.md.

1. Tuning: every sounding note C3-C6 alone (piano profile, no decay), its mean
   pitch against equal temperament, next to a model of the DSP (pitch floored
   to 1/32 semitone, grain period truncated to whole samples, the 0.2 st
   vibrato floor dithering both).
2. Chords: C4-E4-G4 and A3-C4-E4 held on three monks; each note's pitch
   followed through its fundamental (heterodyne), so the intervals between the
   monks can be read as they wobble: own seeds (now), one seed, and the
   vibrato_var settings, and vibrato.lock (the helper key this session added).
3. Decay: Gervill's piano against the profile's level curve.
4. Endings: whether the 'ng' vowel sweep at a note's end flares a harmonic.
5. Drift: how the body's i -> e drift bends the decay, against steady vowels.

Run: py tools/tuning/piano/measure_4c_piano.py [--quick]  (writes renders/tuning/piano/measure/)
"""

import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import piano_phrases as pp  # noqa: E402
from piano_phrases import dl  # noqa: E402

WORK = pp.WORK  # renders/tuning/<family>/, where the output goes

SR = dl.SR
OUT = WORK / "measure"


def nominal(note):
    return 440.0 * 2 ** ((note - 69) / 12)


def model_cents(note, vibrato=0.2, sr=SR):
    """The DSP's mean pitch error (cents) for a sounding note with a sine
    vibrato of `vibrato` st peak: grain_period() floors the pitch to 1/32 st,
    then monk_voice_process truncates the period to whole samples. The mean
    frequency is the grain rate, sr * mean(1 / period)."""
    phase = np.linspace(0, 2 * np.pi, 4096, endpoint=False)
    pitch = note + vibrato * np.sin(phase)
    idx = np.floor(pitch * 32.0)
    freq = 2.0 ** (idx / 384.0) * 8.175799
    period = np.floor(sr / freq)
    mean_hz = sr * np.mean(1.0 / period)
    return 1200 * np.log2(mean_hz / nominal(note))


def tracked(x, f, t0, t1, bw=None):
    """Instantaneous frequency (Hz) and amplitude of the component near f, by an
    FFT band-pass (raised-cosine edges) and the analytic signal."""
    seg = dl.mono(x)[int(t0 * SR):int(t1 * SR)]
    n = len(seg)
    spec = np.fft.fft(seg)
    freqs = np.fft.fftfreq(n, 1 / SR)
    bw = bw or min(30.0, 0.09 * f)
    d = np.abs(freqs - f)
    mask = np.where(d < bw * 0.6, 1.0, np.where(d < bw, 0.5 * (1 + np.cos(np.pi * (d - 0.6 * bw) / (0.4 * bw))), 0.0))
    mask[freqs < 0] = 0
    y = np.fft.ifft(spec * mask * 2)
    phase = np.unwrap(np.angle(y))
    inst = np.diff(phase) * SR / (2 * np.pi)
    amp = np.abs(y[1:])
    edge = int(0.08 * SR)
    return inst[edge:-edge], amp[edge:-edge]


def best_harmonic(x, f0, t0, t1, kmax=4):
    seg = dl.mono(x)[int(t0 * SR):int(t1 * SR)]
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    freqs = np.fft.rfftfreq(len(seg), 1 / SR)
    energy = [spec[np.abs(freqs - k * f0) < 0.03 * k * f0].max() for k in range(1, kmax + 1)]
    return 1 + int(np.argmax(energy))


def held(notes, seconds=4.0, extra=(), monks=None, before=(), stagger=0.0):
    """Notes held together (or `stagger` ms apart, all ending together), after
    an optional melody `before` on the first monk."""
    sections = pp.profile(body={"decay": 0, "vowel": None, "breath": 0.75})
    lead = [(pp.START + k * 300.0, n, 270.0, 80) for k, n in enumerate(before)]
    t0 = pp.START + 300.0 * len(before)
    end = t0 + seconds * 1000
    chord = [(t0 + k * stagger, n, end - t0 - k * stagger, 90) for k, n in enumerate(notes)]
    text = pp.script(pp.Phrase("held", lead + chord), sections, extra)
    return dl.render(text, monks=monks or len(notes), tail=200), t0 / 1000


def tuning(report, quick):
    report += ["## 1. Tuning of single notes", "",
               "Piano profile with no decay, one monk, 4 s; mean pitch of the strongest of the "
               "first four harmonics over 0.6-4.2 s, weighted by its amplitude. Model: the DSP's "
               "two quantizations under the 0.2 st vibrato floor (see the script).", "",
               "| Note | Hz | Period (samples) | Measured (cents) | Model (cents) | Vibrato peak (cents) |",
               "| --- | --- | --- | --- | --- | --- |"]
    rows = []
    notes = range(48, 85, 3 if quick else 1)
    for note in notes:
        x, _ = held([note])
        f0 = nominal(note)
        k = best_harmonic(x, f0, 1.0, 4.0)
        inst, amp = tracked(x, k * f0, 0.6, 4.2)
        w = amp ** 2
        mean = np.sum(inst * w) / np.sum(w) / k
        cents = 1200 * np.log2(mean / f0)
        dev = 1200 * np.log2(np.maximum(inst / k, 1) / mean)
        peak = np.percentile(np.abs(dev), 98)
        model = model_cents(note)
        rows.append((note, cents, model))
        names = "C C# D D# E F F# G G# A A# B".split()
        report.append(f"| {names[note % 12]}{note // 12 - 1} | {f0:.1f} | {SR / f0:.2f} | {cents:+.1f} | "
                      f"{model:+.1f} | {peak:.0f} |")
    report.append("")
    return rows


def chord_wobble(report, label, notes, extra, before=(), stagger=0.0, monks=None):
    x, t0 = held(notes, 6.0, extra, monks, before, stagger)
    a0 = t0 + stagger * (len(notes) - 1) / 1000 + 0.5
    tracks = []
    for n in notes:
        inst, amp = tracked(x, nominal(n), a0, t0 + 6.0)
        tracks.append(1200 * np.log2(np.maximum(inst, 1) / nominal(n)))
    m = min(len(t) for t in tracks)
    tracks = [t[:m] for t in tracks]
    # Smooth over 5 ms: the grain steps are not what the ear follows.
    k = np.ones(240) / 240
    tracks = [np.convolve(t, k, mode="same") for t in tracks]
    out = []
    for a in range(len(notes)):
        for b in range(a + 1, len(notes)):
            iv = tracks[b] - tracks[a]
            out.append((notes[a], notes[b], np.mean(iv), np.percentile(iv, 99) - np.percentile(iv, 1),
                        np.std(iv)))
    worst = max(o[3] for o in out)
    mean_err = [np.mean(t) for t in tracks]
    report.append(f"| {label} | {', '.join(f'{c:+.1f}' for c in mean_err)} | "
                  + "; ".join(f"{o[2]:+.1f} ±{o[4]:.1f} (span {o[3]:.0f})" for o in out) + f" | {worst:.0f} |")
    return worst


def chords(report):
    report += ["## 2. Intervals in a held chord", "",
               "Three monks hold the chord 6 s (no decay). Each note's pitch is followed through "
               "its fundamental and smoothed over 5 ms. For each pair: the mean interval error, its "
               "standard deviation and the 1-99 % span (cents), i.e. how far the interval wobbles "
               "as the monks' vibrato floors (±0.2 st each) run apart.", "",
               "| Setting | Mean error per note (cents) | Interval error: mean ± sd (span) | Worst span |",
               "| --- | --- | --- | --- |"]
    settings = [
        ("now (own seeds, vibrato_var 0.08)", []),
        ("own seeds, vibrato_var 0", [("choir.vibrato_var", 0)]),
        ("own seeds, vibrato_var 0.2", [("choir.vibrato_var", 0.2)]),
        ("one seed, vibrato_var 0 (lockstep)", [("choir.seed", 0), ("choir.vibrato_var", 0)]),
        ("vibrato.lock 1 (new in phase 4c)", [("vibrato.lock", 1)]),
    ]
    for chord in ((60, 64, 67), (57, 60, 64)):
        for label, extra in settings:
            chord_wobble(report, f"{'-'.join(map(str, chord))}: {label}", chord, extra)
    report += ["", "In music the monks' histories differ. The same chord (C4-E4-G4) after five "
               "melody notes on the first monk, and as a pedalled arpeggio (300 ms apart, held "
               "together):", "",
               "| Setting | Mean error per note (cents) | Interval error: mean ± sd (span) | Worst span |",
               "| --- | --- | --- | --- |"]
    for label, extra in settings[:1] + settings[3:]:
        chord_wobble(report, f"after a melody: {label}", (60, 64, 67), extra,
                     before=(72, 71, 69, 67, 65), monks=3)
        chord_wobble(report, f"arpeggio: {label}", (60, 64, 67), extra, stagger=300.0)
    report.append("")


def decay(report):
    """Gervill's piano C4 against the profile: level in dB below the peak."""
    OUT.mkdir(exist_ok=True)
    tmp = OUT / "tmp"
    tmp.mkdir(exist_ok=True)
    report += ["## 3. Decay", "",
               "Level (dB below each note's peak, 50 ms RMS) at times after the onset, single notes "
               "held 6 s. Gervill: its default soundbank, as midis2jam2 plays. Monk: the piano "
               "profile as it is (decay 900 ms at C4, sustain 0, track 0.7; a note ends 40 dB down). "
               "Monk longer: decay 2500 ms at C4, track 0.85 (the candidate).",
               "", "| Note | Source | 0.1 s | 0.3 s | 0.5 s | 1 s | 1.5 s | 2 s | 3 s | 4 s |",
               "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    times = [0.1, 0.3, 0.5, 1, 1.5, 2, 3, 4]
    for note in (48, 60, 72):
        phrase = pp.Phrase("one", [(pp.START, note, 6000.0, 90)])
        pp.write_mid(tmp / "one.mid", {pp.PIANO: (0, phrase.notes, [])})
        g = pp.gervill(tmp / "one.mid", tmp / "one.wav")
        m = dl.render(pp.script(phrase, pp.profile()), monks=1, tail=200)
        longer = dl.render(pp.script(phrase, pp.profile(), [("body.decay", 2500),
                                                            ("body.decay_track", 0.85)]),
                           monks=1, tail=200)
        for label, x in (("Gervill", g), ("Monk now", m), ("Monk longer", longer)):
            mono = dl.mono(x)
            win = int(0.05 * SR)
            rms = np.sqrt(np.convolve(mono ** 2, np.ones(win) / win, mode="same"))
            start = int(pp.START / 1000 * SR)
            peak = rms[start:start + int(0.3 * SR)].max()
            vals = []
            for t in times:
                i = start + int(t * SR)
                vals.append(20 * np.log10(max(rms[i], 1e-9) / peak))
            names = {48: "C3", 60: "C4", 72: "C5"}
            report.append(f"| {names[note]} | {label} | " + " | ".join(f"{v:.0f}" for v in vals) + " |")
    report.append("")


def stft_db(x, t0, t1, win=0.010, hop=0.002, fmax=5000):
    mono = dl.mono(x)
    n = int(win * SR)
    frames = []
    for a in range(int(t0 * SR), int(t1 * SR) - n, int(hop * SR)):
        frames.append(np.abs(np.fft.rfft(mono[a:a + n] * np.hanning(n), 4096)))
    freqs = np.fft.rfftfreq(4096, 1 / SR)
    keep = freqs <= fmax
    return 20 * np.log10(np.array(frames)[:, keep] + 1e-12)


def endings(report):
    """The 'ng' ending moves the vowel e -> 0.15 over the release while the level
    fades. Does that sweep flare a harmonic the way onset moves did (IMITATION.md
    16, phase 4b diagnosis)? Each note held 600 ms, then released."""
    report += ["## 4. Note endings: does the 'ng' sweep flare?", "",
               "Each note held 600 ms with the longer decay (2.5 s at C4), then released "
               "(release 120 ms). 'Rise' is the loudest 10 ms frame of the release against the "
               "note's level just before the key lifts (the level itself falls 26 dB over the "
               "release, so anything above about -2 dB is the sweep). 'Worst bin': the largest "
               "rise of any bin up to 3.5 kHz (below the breath partials) within 40 dB of the "
               "note's loudest, against that bin's own highest level in the 60 ms before.", "",
               "| Note | 'ng' (now): rise | 'ng': worst bin | No 'ng': rise | No 'ng': worst bin |",
               "| --- | --- | --- | --- | --- |"]
    long_ = [("body.decay", 2500), ("body.decay_track", 0.85)]
    names = "C C# D D# E F F# G G# A A# B".split()
    for note in range(48, 85, 4):
        row = []
        for extra in (long_, long_ + [("ending.vowel", -1)]):
            phrase = pp.Phrase("one", [(pp.START, note, 600.0, 90)])
            x = dl.render(pp.script(phrase, pp.profile(), extra), monks=1, tail=400)
            up = (pp.START + 600) / 1000
            before = stft_db(x, up - 0.06, up, fmax=3500)
            after = stft_db(x, up, up + 0.13, fmax=3500)
            body = before.max(axis=0)
            live = body > body.max() - 40
            total = lambda s: 10 * np.log10((10 ** (s / 10)).sum(axis=1))
            rise = total(after).max() - total(before)[-5:].mean()
            row += [f"{rise:+.1f} dB", f"{(after.max(axis=0) - body)[live].max():+.1f} dB"]
        report.append(f"| {names[note % 12]}{note // 12 - 1} | " + " | ".join(row) + " |")
    report.append("")


def drift(report):
    """The profile's body drift (i -> e over 600 ms) against steady vowels: how far
    each note's level strays from a clean exponential decay. Delay Lama's narrow
    formants make loudness depend on where they sit against the harmonics, so a
    moving vowel swells or dips the note."""
    report += ["## 5. Vowel drift and the decay", "",
               "One note held 1.8 s with the longer decay (2.5 s at C4, track 0.85). Level (30 ms "
               "RMS) minus the exponential decay it should follow, 0.05-1.5 s after the onset, "
               "lined up on the first 0.1 s: lowest..highest in dB (+ = the note swells).", ""]
    options = {"drift i>e (now)": [], "steady i": [("body.vowel", -1)],
               "steady ih (0.88)": [("nucleus.vowel", 0.88), ("body.vowel", -1)],
               "steady e (0.75)": [("nucleus.vowel", 0.75), ("body.vowel", -1)]}
    report += ["| Note | " + " | ".join(options) + " |", "| --- |" + " --- |" * len(options)]
    long_ = [("body.decay", 2500), ("body.decay_track", 0.85)]
    names = "C C# D D# E F F# G G# A A# B".split()
    for note in (48, 55, 60, 64, 67, 72, 76, 79, 84):
        row = []
        for extra in options.values():
            phrase = pp.Phrase("one", [(pp.START, note, 1800.0, 90)])
            x = dl.render(pp.script(phrase, pp.profile(), long_ + extra), monks=1, tail=100)
            mono = dl.mono(x)
            win = int(0.03 * SR)
            rms = np.sqrt(np.convolve(mono ** 2, np.ones(win) / win, mode="same"))
            start = int(pp.START / 1000 * SR)
            T = 2.5 * 0.85 ** ((note - 60) / 12)
            ts = np.arange(0.05, 1.5, 0.01)
            level = np.array([20 * np.log10(rms[start + int(t * SR)] + 1e-12) for t in ts])
            d = level + 26.06 * ts / T
            d -= np.median(d[:10])
            row.append(f"{d.min():+.1f}..{d.max():+.1f}")
        report.append(f"| {names[note % 12]}{note // 12 - 1} | " + " | ".join(row) + " |")
    report.append("")


def main():
    quick = "--quick" in sys.argv
    OUT.mkdir(exist_ok=True)
    report = ["# Piano: measurements", "",
              "Written by `measure_4c_piano.py` (DelayLamaVoice in profile mode, 48 kHz).", ""]
    tuning(report, quick)
    chords(report)
    decay(report)
    endings(report)
    drift(report)
    (OUT / "measurements.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
