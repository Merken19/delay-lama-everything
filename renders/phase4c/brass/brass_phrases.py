"""Phase 4c brass and sax families (GM 57-68; profiles `trumpet`, `trombone`,
`tuba`, `brass.section`, `sax.alto`, `sax.tenor`): test phrases, MIDI files and
DelayLamaVoice scripts. Dev tool, never packaged; measure_4c_brass.py and
make_4c_brass.py use it. The MIDI writer, the Gervill renderer and the script
builder come from the piano set (renders/phase4c/piano/piano_phrases.py), as in
renders/phase4c/pipe/pipe_phrases.py.

Every phrase is original, in C at 100 bpm with a 500 ms lead-in, over one
eight-bar progression (C | Am | F | G | C | Am | Dm G | C). Tongued notes are
85% of their step; slurred notes overlap the next by 30 ms (the router's auto
mode reads 10 ms or more as legato). Sounding pitches (GM plays as written).
The MIDI files land in midi/:

  trumpet.mid       eight bars of tongued trumpet lead G4-F5, median C5 (so D37
                    leaves it as written, as c03 was), with seven A4 and seven
                    E5 onsets (where c03's "very high pitch" was measured) and
                    repeated E5 eighths
  sax.mid           eight bars of tenor sax, mostly slurred, E3-G4 (c04 was
                    A3-E4, slurred "doo-ah")
  trombone.mid      sax.mid an octave down (C2-G3)
  tuba.mid          sax.mid two octaves down
  horn.mid          sax.mid as written (a horn's middle)
  band.mid          call and response over Gervill piano comping (channel 3),
                    finger bass (4) and drums (10): the trumpet (channel 1)
                    plays bars 1-2 and 5-6 of trumpet.mid, the tenor sax
                    (channel 2) bars 3-4 and 7-8 of sax.mid
  band_rest.mid     band.mid without trumpet and sax

Rendering uses a copy of DelayLamaVoice.exe in tmp/ (fresh at every run), so
a render never locks the helper's build folder while another session rebuilds.
"""

import pathlib
import shutil
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / "piano"))
import piano_phrases as pp  # noqa: E402
from piano_phrases import Phrase, dl, expand, BEAT, Q, E, S, H, W, START  # noqa: E402

TMP = HERE / "tmp"

TRUMPET, SAX, PIANO, BASS, DRUMS = 0, 1, 2, 3, 9
PROGRAM = {"trumpet": 56, "trombone": 57, "tuba": 58, "muted": 59, "horn": 60, "section": 61,
           "alto": 65, "tenor": 66}

TONGUED = 0.85
SLUR = 30.0


def use_exe_copy():
    """Copy the helper into tmp/ and make dl.render use the copy."""
    TMP.mkdir(exist_ok=True)
    copy = TMP / "DelayLamaVoice.exe"
    for attempt in range(10):
        try:
            shutil.copy2(dl.EXE, copy)
            break
        except OSError:
            if attempt == 9:
                raise
            time.sleep(60)
    defaults = list(dl.render.__defaults__)
    defaults[0] = copy
    dl.render.__defaults__ = tuple(defaults)
    return copy


def notes_from(tune, start=START, velocity=88, tongued=TONGUED):
    """tune: (note, length, slur-to-next) per note; rests as note None."""
    notes, t = [], start
    for k, (n, d, slur) in enumerate(tune):
        if n is not None:
            length = d + SLUR if slur else d * tongued
            v = velocity + (8 if k % 4 == 0 else 0)
            notes.append((t, n, length, v))
        t += d
    return notes


DQ = Q + E  # dotted quarter

# Two bars per row; (note, length, slur to next).
TRUMPET_TUNE = [
    [(67, E, False), (72, E, False), (76, Q, False), (76, E, False), (74, E, False), (72, Q, False),
     (69, DQ, False), (67, E, False), (69, H, False)],
    [(65, E, False), (69, E, False), (72, Q, False), (69, E, False), (72, E, False), (77, Q, False),
     (76, E, False), (74, E, False), (71, Q, False), (67, H, False)],
    [(76, E, False), (76, E, False), (76, E, False), (74, E, False), (72, Q, False), (67, Q, False),
     (69, E, False), (71, E, False), (72, E, False), (76, E, False), (69, H, False)],
    [(65, E, False), (69, E, False), (74, Q, False), (71, E, False), (67, E, False), (71, Q, False),
     (72, W * 0.75, False), (None, W * 0.25, False)],
]

SAX_TUNE = [
    [(52, Q, True), (55, Q, True), (60, Q, True), (64, Q, False),
     (62, E, True), (60, E, False), (57, H + Q, False)],
    [(57, E, True), (60, E, True), (65, Q, False), (64, E, True), (62, E, True), (60, Q, False),
     (59, Q, True), (62, Q, True), (55, H, False)],
    [(55, E, False), (57, E, False), (60, E, True), (62, E, True), (64, Q, False), (67, Q, False),
     (64, Q, True), (62, E, True), (60, E, False), (57, H, False)],
    [(53, E, True), (57, E, True), (62, Q, False), (59, E, True), (62, E, True), (55, Q, False),
     (60, W * 0.75, False), (None, W * 0.25, False)],
]


def tune(rows, which=(0, 1, 2, 3)):
    """The rows in `which`, the others as rests (2 bars each)."""
    out = []
    for k, row in enumerate(rows):
        out += row if k in which else [(None, 2 * W, False)]
    return out


def trumpet(which=(0, 1, 2, 3)):
    return Phrase("trumpet", notes_from(tune(TRUMPET_TUNE, which)))


def sax(which=(0, 1, 2, 3), transpose=0, name="sax"):
    notes = notes_from(tune(SAX_TUNE, which), velocity=84)
    return Phrase(name, [(t, n + transpose, d, v) for t, n, d, v in notes])


# --- the band (Gervill) ----------------------------------------------------------------

CHORDS = [[(60, 64, 67)], [(57, 60, 64)], [(57, 60, 65)], [(55, 59, 62)],
          [(60, 64, 67)], [(57, 60, 64)], [(57, 62, 65), (55, 59, 65)], [(60, 64, 67)]]
ROOTS = [[36], [33], [29], [31], [36], [33], [38, 31], [36]]


def piano_part():
    """Chords on beats 2 and 4 (and the last bar held)."""
    notes = []
    for bar, chords in enumerate(CHORDS):
        t0 = START + bar * W
        if bar == 7:
            notes += [(t0, n, W * 0.9, 62) for n in chords[0]]
            continue
        for beat in (1, 3):
            chord = chords[0] if len(chords) == 1 or beat == 1 else chords[1]
            notes += [(t0 + beat * Q, n, Q * 0.6, 60) for n in chord]
    return notes


def bass_line():
    notes = []
    for bar, roots in enumerate(ROOTS):
        t0 = START + bar * W
        if bar == 7:
            notes.append((t0, roots[0], W * 0.9, 92))
        elif len(roots) == 2:
            notes += [(t0, roots[0], H * 0.9, 92), (t0 + H, roots[1], H * 0.9, 90)]
        else:
            notes += [(t0, roots[0], Q * 0.9, 94), (t0 + Q + E, roots[0], E * 0.8, 80),
                      (t0 + H, roots[0] + 7, Q * 0.9, 88), (t0 + H + Q, roots[0] + 12, Q * 0.8, 84)]
    return notes


def drum_hits():
    hits = []
    for bar in range(7):
        t = START + bar * W
        hits += [(t + k * E, 42, 55) for k in range(8)]
        hits += [(t, 36, 95), (t + 2 * Q + E, 36, 80), (t + Q, 38, 85), (t + 3 * Q, 38, 85)]
    hits += [(START + 7 * W, 36, 100), (START + 7 * W, 49, 90)]
    return [(t, n, 120.0, v) for t, n, v in hits]


def band_trumpet():
    p = trumpet((0, 2))
    return Phrase("band_trumpet", p.notes)


def band_sax():
    p = sax((1, 3))
    return Phrase("band_sax", p.notes)


def band_parts(horns=True):
    parts = {PIANO: (4, piano_part(), []), BASS: (33, bass_line(), []), DRUMS: (0, drum_hits(), [])}
    if horns:
        parts[TRUMPET] = (PROGRAM["trumpet"], band_trumpet().notes, [])
        parts[SAX] = (PROGRAM["tenor"], band_sax().notes, [])
    return parts


def lines():
    """(phrase, Gervill program, profile) for each line the measurements use."""
    return [(trumpet(), PROGRAM["trumpet"], "trumpet"),
            (sax(), PROGRAM["tenor"], "sax.tenor"),
            (sax(name="alto", transpose=7), PROGRAM["alto"], "sax.alto"),
            (sax(name="trombone", transpose=-12), PROGRAM["trombone"], "trombone"),
            (sax(name="tuba", transpose=-24), PROGRAM["tuba"], "tuba"),
            (sax(name="horn"), PROGRAM["horn"], "brass.section"),
            (trumpet(), PROGRAM["section"], "brass.section")]


def write_all_midi(folder=HERE / "midi"):
    folder.mkdir(exist_ok=True)
    for phrase, program, _ in lines()[:6]:
        pp.write_mid(folder / f"{phrase.name}.mid", {0: (program, phrase.notes, [])})
    pp.write_mid(folder / "band.mid", band_parts())
    pp.write_mid(folder / "band_rest.mid", band_parts(horns=False))
    for name, phrase, program in (("band_trumpet", band_trumpet(), PROGRAM["trumpet"]),
                                  ("band_sax", band_sax(), PROGRAM["tenor"])):
        pp.write_mid(folder / f"{name}.mid", {0: (program, phrase.notes, [])})


# --- scripts --------------------------------------------------------------------------

def profile(name, data=None, **override):
    data = data or expand.load()
    return expand.merge(expand.resolve(data, name), override)


def script(phrase, sections, extra=(), fit=True, shift=None):
    """As the router sends it: the profile, then range.shift from the phrase's
    notes (D37: down by octaves while the median is above range.high)."""
    if shift is None:
        shift = expand.fit_shift(sections, [n for _, n, _, _ in phrase.notes]) if fit else 0
    return pp.script(phrase, sections, list(extra) + [("range.shift", shift)])


def shift_of(phrase, sections):
    return expand.fit_shift(sections, [n for _, n, _, _ in phrase.notes])
