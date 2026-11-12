"""Shared helpers for the tuning tools: render a DelayLamaVoice script,
read WAVs, track pitch, and draw spectrograms. Dev tool, never packaged."""

import pathlib
import subprocess
import tempfile
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXE = ROOT / "external" / "delalalalay-lama" / "Windows" / "build" / "Release" / "DelayLamaVoice.exe"
SR = 48000


def read_wav(path):
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
    return x.reshape(-1, 2) / 32768


def write_wav(path, x):
    x = np.asarray(x)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def render(script, exe=EXE, monks=1, tail=300, out=None):
    """Renders script text (or a path) and returns the stereo float array."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        if isinstance(script, pathlib.Path):
            path = script
        else:
            path = tmp / "script.txt"
            path.write_text(script, encoding="utf-8")
        wav = pathlib.Path(out) if out else tmp / "out.wav"
        r = subprocess.run([str(exe), "--render", str(path), str(wav), "--monks", str(monks),
                            "--tail", str(tail)], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(r.stdout + r.stderr)
        return read_wav(wav)


def mono(x):
    return x.mean(axis=1) if x.ndim == 2 else x


def yin(x, t0, t1, fmin=40, fmax=1500, win=0.04, hop=0.001, threshold=0.15):
    """YIN pitch track of mono x between t0 and t1 s. Returns (times, hz, aperiodicity)."""
    w = int(win * SR)
    lag_max = int(SR / fmin)
    lag_min = int(SR / fmax)
    times, f0s, ap = [], [], []
    t = t0
    while t < t1:
        c = int(t * SR)
        a = c - w // 2
        if a < 0 or a + w + lag_max >= len(x):
            t += hop
            continue
        seg = x[a:a + w + lag_max]
        frame = seg[:w]
        d = np.zeros(lag_max + 1)
        e0 = np.sum(frame * frame)
        for lag in range(1, lag_max + 1):
            diff = frame - seg[lag:lag + w]
            d[lag] = np.dot(diff, diff)
        cmnd = np.ones_like(d)
        run = np.cumsum(d[1:])
        cmnd[1:] = d[1:] * np.arange(1, lag_max + 1) / np.maximum(run, 1e-12)
        lag = None
        for k in range(lag_min, lag_max):
            if cmnd[k] < threshold and cmnd[k] <= cmnd[k + 1]:
                lag = k
                break
        if lag is None:
            lag = lag_min + int(np.argmin(cmnd[lag_min:lag_max]))
        if 1 <= lag < lag_max:
            y0, y1, y2 = cmnd[lag - 1], cmnd[lag], cmnd[lag + 1]
            den = y0 - 2 * y1 + y2
            frac = 0.5 * (y0 - y2) / den if abs(den) > 1e-12 else 0.0
        else:
            frac = 0.0
        times.append(t)
        f0s.append(SR / (lag + frac) if e0 > 1e-9 else np.nan)
        ap.append(cmnd[lag])
        t += hop
    return np.array(times), np.array(f0s), np.array(ap)


def hz_to_note(hz):
    return 69 + 12 * np.log2(np.asarray(hz) / 440.0)


def spectrogram_png(x, path, t0, t1, fmax=6000, win=0.010, hop=0.0005, title="", marks=()):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = mono(x)
    n = int(win * SR)
    h = int(hop * SR)
    a, b = int(t0 * SR), int(t1 * SR)
    seg = x[a:b]
    frames = []
    for i in range(0, max(1, len(seg) - n), h):
        frames.append(np.abs(np.fft.rfft(seg[i:i + n] * np.hanning(n), 4096)))
    S = 20 * np.log10(np.array(frames).T + 1e-9)
    freqs = np.fft.rfftfreq(4096, 1 / SR)
    keep = freqs <= fmax
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=90)
    top = S[keep].max()
    ax.imshow(S[keep], origin="lower", aspect="auto", vmin=top - 70, vmax=top, cmap="magma",
              extent=[t0 * 1000, t1 * 1000, 0, fmax])
    for m in marks:
        ax.axvline(m * 1000, color="cyan", lw=0.6)
    ax.set_xlabel("ms")
    ax.set_ylabel("Hz")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def band_db(x, t0, t1, lo, hi, win=0.005, hop=0.001):
    """Short-time level (dB) of mono x in the lo-hi Hz band."""
    x = mono(x)
    n = int(win * SR)
    out_t, out = [], []
    freqs = np.fft.rfftfreq(2048, 1 / SR)
    sel = (freqs >= lo) & (freqs < hi)
    t = t0
    while t < t1:
        a = int(t * SR)
        f = np.fft.rfft(x[a:a + n] * np.hanning(n), 2048)
        out_t.append(t)
        out.append(10 * np.log10(np.sum(np.abs(f[sel]) ** 2) + 1e-12))
        t += hop
    return np.array(out_t), np.array(out)
