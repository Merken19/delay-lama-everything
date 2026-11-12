"""Pipe family (GM 73-80, profile `flute`): test phrases, MIDI files and
DelayLamaVoice scripts. Dev tool, never packaged; measure_4c_pipe.py and
make_4c_pipe.py use it. The MIDI writer, the Gervill renderer and the script
builder come from the piano set (tools/tuning/piano/piano_phrases.py).

Every phrase is original, at 100 bpm with a 500 ms lead-in, written where a
flute plays (E5-A6 mostly; one low line G4-E5). Tongued notes are 85% of their
step; slurred notes overlap the next by 30 ms, as a keyboard player's legato
(the router's auto mode reads an overlap of 10 ms or more as legato). The MIDI
files land in renders/tuning/pipe/midi/:

  tongued.mid     tongued eighths up and down A5-E6, then repeated E6s
                  (eighths, sixteenths)
  slurred.mid     a slurred cantabile line in quarters and halves (E5-A6)
  run.mid         a fast slurred run D5-D6-D5, 100 ms per note
  long.mid        long A5 and long E6 (3 s each), for the vibrato
  low.mid         a tongued line low in the flute (G4-E5)
  melody.mid      eight bars mixing slurred pairs and tongued notes (E5-A6)
  lines.mid       tongued, slurred, run and long in one file
  band.mid        melody (channel 1, flute) with string pad (2), finger bass
                  (3) and light drums (10)
  band_no_flute.mid
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / "piano"))
import piano_phrases as pp  # noqa: E402
from piano_phrases import Phrase, dl, expand, BEAT, Q, E, S, H, W, START  # noqa: E402

WORK = pp.work_dir("pipe")

FLUTE, PAD, BASS, DRUMS = 0, 1, 2, 9
FLUTE_PROGRAM = 73  # GM Flute, 0-based

TONGUED = 0.85
SLUR = 30.0


def notes_from(tune, start=START, velocity=84):
    """tune: (note, length, slur-to-next) per note; rests as note None."""
    notes, t = [], start
    for k, (n, d, slur) in enumerate(tune):
        if n is not None:
            length = d + SLUR if slur else d * TONGUED
            v = velocity + (6 if k % 4 == 0 else 0)
            notes.append((t, n, length, v))
        t += d
    return notes


def tongued():
    up = [81, 83, 85, 86, 88, 86, 85, 83]
    tune = [(n, E, False) for n in up] + [(81, Q, False)]
    tune += [(88, E, False)] * 4 + [(88, S, False)] * 8 + [(86, Q, False)]
    return Phrase("tongued", notes_from(tune))


def slurred():
    tune = [(76, Q, True), (79, Q, True), (83, Q, True), (81, Q, False),
            (84, H, True), (83, Q, True), (79, Q, False),
            (81, Q, True), (86, Q, True), (88, Q, True), (93, Q, True),
            (91, H, True), (88, H, False)]
    return Phrase("slurred", notes_from(tune, velocity=78))


def run():
    up = [74, 76, 78, 79, 81, 83, 85, 86]
    tune = [(n, 100.0, True) for n in up + up[-2::-1]]
    tune[-1] = (74, Q, False)
    return Phrase("run", notes_from(tune, velocity=80))


def long_notes():
    return Phrase("long", [(START, 81, 3000.0, 84), (START + 3600, 88, 3000.0, 84)])


def low():
    tune = [(67, E, False), (69, E, False), (71, E, False), (72, E, False), (74, Q, False), (76, Q, False),
            (74, E, False), (72, E, False), (71, E, False), (69, E, False), (67, H, False)]
    return Phrase("low", notes_from(tune, velocity=80))


MELODY = [
    # bar 1-2: slurred pairs, then tongued
    (81, E, True), (83, E, False), (85, E, True), (86, E, False), (88, Q, False), (86, Q, False),
    (85, E, True), (83, E, False), (81, E, False), (78, E, False), (81, H, False),
    # bar 3-4: a slurred climb to A6 and a long note
    (79, E, True), (81, E, True), (83, E, True), (86, E, False), (88, E, True), (91, E, True), (93, Q, False),
    (91, Q, True), (88, Q, True), (86, H, False),
    # bar 5-6: repeated tongued notes and a turn
    (88, E, False), (88, E, False), (88, E, False), (86, E, False), (85, E, True), (86, E, True), (88, Q, False),
    (83, E, False), (83, E, False), (83, E, False), (81, E, False), (79, E, True), (81, E, True), (83, Q, False),
    # bar 7-8: a slurred run down and the final note
    (86, S, True), (85, S, True), (83, S, True), (81, S, True), (79, S, True), (78, S, True), (76, S, True),
    (78, S, False), (81, Q, False), (None, Q, False),
    (76, Q, True), (81, W * 0.75, False),
]


def melody(start=START):
    return Phrase("melody", notes_from(MELODY, start))


def lines():
    return pp.chain("lines", [tongued(), slurred(), run(), long_notes()])


# --- the band under melody() (Gervill) -----------------------------------------------

CHORD_BARS = [(57, 61, 64), (57, 62, 66), (54, 57, 61), (59, 62, 66),
              (57, 61, 64), (59, 62, 66), (57, 61, 64), (57, 61, 64)]
ROOTS = [45, 50, 42, 47, 45, 47, 40, 45]


def pad_part():
    notes = []
    for bar, chord in enumerate(CHORD_BARS):
        notes += [(START + bar * W, n, W - 20, 64) for n in chord]
    return notes


def bass_line():
    notes = []
    for bar, root in enumerate(ROOTS):
        t0 = START + bar * W
        notes += [(t0, root, H * 0.9, 92), (t0 + H, root + 7 if bar < 7 else root, H * 0.9, 86)]
    return notes


def drum_hits():
    hits = []
    for bar in range(8):
        t = START + bar * W
        hits += [(t + k * E, 42, 50) for k in range(8)]
        hits += [(t, 36, 90), (t + 2 * Q, 36, 85), (t + Q, 37, 60), (t + 3 * Q, 37, 60)]
    return [(t, n, 120.0, v) for t, n, v in hits]


def band_parts(flute=True):
    parts = {PAD: (48, pad_part(), []), BASS: (33, bass_line(), []), DRUMS: (0, drum_hits(), [])}
    if flute:
        parts[FLUTE] = (FLUTE_PROGRAM, melody().notes, [])
    return parts


def write_all_midi(folder=WORK / "midi"):
    folder.mkdir(exist_ok=True)
    for phrase in (tongued(), slurred(), run(), long_notes(), low(), melody(), lines()):
        pp.write_mid(folder / f"{phrase.name}.mid", {FLUTE: (FLUTE_PROGRAM, phrase.notes, [])})
    pp.write_mid(folder / "band.mid", band_parts())
    pp.write_mid(folder / "band_no_flute.mid", band_parts(flute=False))


# --- scripts --------------------------------------------------------------------------

def profile(name="flute", data=None, **override):
    data = data or expand.load()
    return expand.merge(expand.resolve(data, name), override)


def script(phrase, sections, extra=(), fit=True, shift=None):
    """As the router sends it: the profile, then range.shift from the phrase's
    notes (the octave fold: down by octaves while the median is above range.high)."""
    if shift is None:
        shift = expand.fit_shift(sections, [n for _, n, _, _ in phrase.notes]) if fit else 0
    return pp.script(phrase, sections, list(extra) + [("range.shift", shift)])


def shift_of(phrase, sections=None):
    return expand.fit_shift(sections or profile(), [n for _, n, _, _ in phrase.notes])
