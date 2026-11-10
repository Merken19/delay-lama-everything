# Instrument imitation

How Delay Lama imitates each instrument, as implemented by the articulator
in `DelayLamaVoice.exe` (profile mode) and the data in
`profiles/imitation.json`. Profiles use all of Delay Lama's parameters. §15
is the tuning method, and §16 what the DSP's limits mean for profiles and
where the tuned families stand.

## 1. The goal

When a person "plays" an instrument with their voice, they don't hold a
vowel. They shape each note like a syllable: a guitar riff becomes
"nyeow-nyeow-dang", a bass line "dum dum doon", a flute "hoo-too-hoo". The
imitation lives in how each note **starts**, **moves** and **ends**, in the
voice's register and vibrato, and in how notes join. Since the monk's mouth
follows the vowel, the monks also *look* like they are imitating.

The character is **musical**: profiles imitate the way a good a
cappella singer would. An **exaggeration** amount (0–2, default 1, one
value for all channels) scales the expressive moves.

## 2. The palette

These are the DSP facts that matter for imitation (`external/delalalalay-lama/DSP/`). The voice sounds like singing from sounding
C2 to C5. Outside that range it still works for imitation.

| Parameter | Range | What it really does | Consequence for the articulator |
| --- | --- | --- | --- |
| Pitch | MIDI note + bend ±12 st | **Sounds one octave below the note** (`grain_period` uses `note − 12`). Mean error +2 to +11 cents, about a piano's stretch | The helper adds 12 to sing the written pitch; profiles talk in written pitch |
| Low limit | | Grains are 20 ms long, so below a sounding ~50 Hz they stop overlapping and the voice becomes a pulse train | The lowest bass notes buzz |
| High limit | | ~15 dB quieter at a sounding 2 kHz. Above ~400 Hz the loudness jumps 5–8 dB from note to note (harmonics against formants), and pitch moves in whole-sample steps (§16) | High parts fold down (§7.1) |
| **Vowel** | 0–1 | Three formants on a spline through **u (0), o (0.25), a (0.5), e (0.75), i (1)**: F1 280/450/800/350/270 Hz, F2 600/800/1150/2000/2140, F3 2240/2830/2900/2800/2950 (`voice.c:29`) | Any move passes the vowels in between: i→u is "ee-eh-ah-oh-oo" |
| Vowel timing | | Read once per grain (once per pitch period); moves under ~25 ms sound like a step | The articulator draws every curve at 1 ms |
| Mouth picture | frames 6–29 | Frame `6 + round(23 × vowel)`; sheet column 0 (closed lips) is idle-only in the standalone | Closed lips can show closures (§10) |
| Voice | 0–1 | Formant scale `0.75 + 0.5 × voice`, from big and dark to small and bright | Body size per instrument, a subtle control |
| Formants | ×0–2 each | All three equally loud and narrow (32.5 / 47.5 / 62.5 Hz) | `voice.formant1`–`3` scale them (§7.8) |
| Vibrato depth | 0–1 | Peak deviation **depth + 0.2 st**, so it never stops | "Straight" is depth 0, at ±0.2 st; sung leads use 0.15, at ±0.35 st |
| Vibrato rate | 0–1 | ≈ 6 × 4^(2r−1) Hz, jittered: 1.4 Hz at 0, 5.9 at 0.5, 24 at 1 (a growl) | Profiles give Hz; choir monks get their own seeds (§9) |
| Breath | 0–1 | Two damped partials (~3.8 and ~4.95 kHz) in every grain: a ping per pitch period, not noise | 0.75 by default; bursts are colour only |
| Glide (DSP) | 0–1 | Constant slew of 12 / (glide + 0.01) st/s; a fifth takes 288 ms at 0.5 | The legato glide (§6) |
| Level | 0–1 | One-pole ~5 ms, applied **after the echo** | The helper owns the echo (§11) |
| Echo, envelope | | The DSP's own | Not used in profile mode |
| Unison | 1–10, cents, spread | Detuned copies, gain 1/√n | Ensembles and pads |
| Velocity | | Ignored by the DSP | The helper turns it into level (§7.10) |

**What it can't do**: no unvoiced sound (no "t", "k", "s" noise), no nasal
murmur as such, only three formants, one note per synth. Consonants are
**suggested** by a level dip, the attack, closed lips and a pitch scoop. A
noise layer lost to pure Delay Lama by ear, and onset vowel moves glitch
(§16).

## 3. How people imitate instruments

- Imitators reproduce a sound's **loudness envelope, tail length, pitch
  contour and brightness**, and simplify the attack
  ([Lemaitre et al.](https://hal.archives-ouvertes.fr/hal-01256126);
  [Delgado et al. 2020](https://comma.eecs.qmul.ac.uk/assets/pdf/delgado_timbre_2020.pdf)).
  Priority for profiles: envelope and tail first, then pitch contour, then
  brightness.
- A cappella syllables follow their role: soft onsets (d, l, n, w) for
  legato, hard ones (t, k, p, b) for accents, nasal endings (m, n, ng) for
  ringing notes, stop endings for damped ones, and brighter vowels for higher
  and harder notes
  ([Bauer](https://journals.library.columbia.edu/index.php/currentmusicology/article/download/4828/2177/8416)).
  Arrangers use "dum" for bass and "wah"/"bow" for distorted guitar.
- The Mills Brothers made the tuba with "the largest possible room in the
  mouth": a dark vowel and a big voice.

## 4. The model

A **profile** is data. The **articulator** applies the profile of the
channel's current program to every note, per monk.

- Each note runs through **onset → nucleus → body → ending**. Consecutive
  notes on one monk are joined by a **phrasing** transition: new,
  re-articulated or legato.
- Every 1 ms tick it computes each monk's vowel, breath, level, pitch
  offset, vibrato, voice size and mouth, calls the DSP setters, and renders
  that monk's next 1 ms. The DSP envelope and echo are off. Notes are shaped
  through the level, and one echo runs on the choir mix.
- A note **snapshots** its profile at the onset, so a profile change applies
  to notes that start later. Ensemble, choir and space keys apply at once.
- A profile is numbers, optionally with a **syllable** shorthand ("d-a-ng")
  that expands to numbers. Explicit numbers win.

Units: times in **ms** (a move's time is the time to complete it; for `exp`,
95 % of the way). Vowels are 0–1 on the axis above. Pitch offsets are in
**semitones**, with pitches given as written MIDI notes unless marked
sounding. Levels inside a note are linear fractions of the note's level.
Vibrato is depth in semitones (peak) and rate in Hz.

## 5. Curves

A move from *a* to *b* over *T* is *a* + (*b* − *a*) × *s*(*x*), with
*x* = *t* / *T* clamped to 0–1:

| Code | Name | *s*(*x*) | Use |
| --- | --- | --- | --- |
| 0 | `step` | 0 for *x* < 1, then 1 | hold, then jump at *T* |
| 1 | `linear` | *x* | attacks, vibrato fade-in |
| 2 | `exp` | (1 − e^(−3x)) / (1 − e^(−3)) | scoops, slews, vowel drift |
| 3 | `ease` | 3x² − 2x³ | vowel moves and glides |
| 4 | `late` | x² | falls and closures |

Level **decays** are exponential toward a floor: level(*t*) = *s* + (1 − *s*)
× e^(−3*t*/*T*). Releases use the same form toward 0. A note ends (the DSP
note-off) 40 dB below where its ending started, or at 1.5 × the release
time.

## 6. Per-note behaviour

For a note with written pitch *n*, velocity *v* and sounding pitch
*n*s = *n* + `range.shift`:

1. **Pitch**: the DSP note is *n*s + 12. The pitch offset combines the
   file's bend (pitch bend is pitch bend, not the standalone's vowel wheel), the onset scoop and the ending fall (plus a drawn glide
   when `phrase.glide_mode` is 1). It goes out as one bend, clamped to
   ±12 st. A legato note sets the DSP glide to `phrase.glide` just before it
   starts; new and re-articulated notes set the glide to 0.
2. **Nucleus vowel** *V* = `nucleus.vowel` + `nucleus.pitch_track` ×
   (*n*s − 60) / 12 + `nucleus.velocity_track` × (*v* − 64) / 63, clamped
   to 0–1.
3. **Vowel**: the note starts on *V* (onsets are steady, §16). A profile
   can set `onset.vowel` to move from it over `onset.time`. The vowel then
   drifts toward `body.vowel` (`exp`, `body.vowel_time`). In the ending it
   moves toward `ending.vowel` over `ending.vowel_time` (`ease`). On a
   legato note it moves from the previous vowel over
   `phrase.legato_vowel_time`.
4. **Level**: a re-articulated note first holds `phrase.dip_level` for
   `phrase.dip_time`. The attack rises linearly over `onset.attack` to
   `onset.peak`; 0 is crisp, with the level preset before the note-on. Then
   comes an exponential decay toward `body.sustain` × peak over `body.decay`
   (scaled by `body.decay_track` per octave above sounding C4), times the
   tremolo, then the release. A legato note keeps the previous level and
   moves to the body level over 40 ms.
5. **Breath**: `onset.burst` falls to `body.breath` over `onset.burst_time`.
   During the release the breath is `ending.breath` if set. The burst grows
   with velocity by `dyn.burst_velocity`.
6. **Vibrato**: the floor until `vibrato.delay`, then a linear rise to
   `vibrato.depth` over `vibrato.fade`, plus `vibrato.modwheel` × CC1/127.
7. **Exaggeration** *x* (0–2) scales the distance from the plain value of
   the vowels, the scoop and fall, the vibrato above the floor, the burst,
   the dip depth and the tracking amounts.
8. **Fast notes**: with `phrase.compress` on, the onset, scoop, attack,
   burst and dip times are multiplied by *k* = clamp(*d* / (3 × *T*), 0.25, 1).
   *T* is the longest of those times and *d* the note's length (from `on`, or
   else the last inter-onset interval).

## 7. Profile parameters

JSON nests the keys by section, and `set` keys are `section.param`. "null"
means "follow the nucleus" and is sent as −1. The full list with ranges is
`Windows/voice_profile_keys.inc` in delalalalay-lama.

### 7.1 `range`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `octave` | −3..+3 | 0 | Shift from the written pitch |
| `fit` | 0 off, 1 octaves, 2 down | 2 | Router-side shift of the whole channel by octaves. 2: down while the channel's median is above `high` (C5 by default); it never shifts up, so a line keeps its shape. 1: median nearest `target` |
| `target` | sounding note | 57 | For `fit` 1 |
| `low`, `high` | sounding notes | 36, 72 | `high` is `fit` 2's ceiling; both bound `fold` |
| `fold` | 0/1 | 0 | Fold single notes outside `low`..`high` (breaks a line's shape, so off) |

The router computes the fit from the whole file, one shift per channel and
profile (`ImitationProfiles.fitShift`, `fit_shift` in `expand.py`), and sends
`set range.shift`.

### 7.2 `onset`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `vowel` | 0–1, null | null | Start vowel. null is steady (§16) |
| `time` | 0–300 | 0 | Move from `vowel` to the nucleus |
| `curve` | 0–4 | 3 | Shape of that move |
| `burst` | 0–1, null | null | Breath at the onset (colour) |
| `burst_time` | 0–150 | 0 | Burst falls to `body.breath` |
| `scoop` | −12..+12 st | 0 | Start this far from the note and approach it |
| `scoop_time` | 0–300 | 0 | |
| `scoop_curve` | 0–4 | 2 | |
| `attack` | 0–2000 | 0 | Level rise; 0 = crisp |
| `peak` | 0–1.5 | 1 | Level at the end of the attack |
| `lips` | 0/1 | 0 | Closed-lips mouth during the onset (b, p, m, w) |
| `mask`, `bandwidth`, `after_rest` | | 0, 1, 0 | Experiment keys, off, since none saved a glitch or consonant by ear: a masking attack, wider formants during an onset move, a move only after a rest |

### 7.3 `nucleus`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `vowel` | 0–1 | 0.5 | The main vowel |
| `pitch_track` | −0.3..+0.3 per octave | 0.05 | Brighter when higher (0 for the bass, §16) |
| `velocity_track` | −0.3..+0.3 | 0 | Vowel change from velocity 64 to 127 |

### 7.4 `body`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `breath` | 0–1 | 0.75 | Breath while sounding |
| `decay` | 0 or 10–10000 | 0 | Exponential fall toward `sustain`; 0 = none |
| `sustain` | 0–1 | 1 | Floor of the decay, as a fraction of the peak |
| `decay_track` | 0.5–1.5 per octave | 1 | Decay time factor per octave above sounding C4 |
| `vowel` | 0–1, null | null | Drift target while sounding |
| `vowel_time` | 0–5000 | 0 | |
| `max` | 0 or 20–5000 | 0 | Staccato cap: the ending starts after this |
| `tremolo` | 0–1 | 0 | Level wobble depth |
| `tremolo_rate` | 0.5–30 Hz | 6 | |
| `end_db` | −60..−20 | −40 | A decaying note below this frees its monk |

### 7.5 `ending`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `release` | 5–5000 | 20 | Exponential fade after the note-off |
| `vowel` | 0–1, null | null | Closing vowel: 0 "m"/"w", 0.15 "ng", 0.85 "n" |
| `vowel_time` | 0–2000, null | null (= release) | |
| `fall` | −12..+12 st | 0 | Pitch fall-off, or a rise |
| `fall_time` | 0–1000 | 0 | `late` curve |
| `breath` | 0–1, null | null | Breath during the release |
| `lips` | 0/1 | 0 | Closed mouth at the end ("m") |

### 7.6 `phrase`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `mode` | 0 auto, 1 legato, 2 rearticulate, 3 detached | 0 | How connected notes join (§8) |
| `gap` | 0–200 | 30 | A note starting within this time after the previous one ended is connected |
| `overlap` | 0–200 | 10 | In auto mode, an overlap at least this long means legato |
| `glide_mode` | 0 rate, 1 time | 0 | The DSP glide, or a glide drawn through the bend |
| `glide` | 0.002–1 | 0.5 | Mode 0: 12 / (glide + 0.01) st/s |
| `glide_time` | 0–500 | 60 | Mode 1 |
| `glide_curve` | 0–4 | 3 | Mode 1 |
| `legato_vowel_time` | 0–500 | 80 | The vowel's move during a slur |
| `dip_time` | 0–80 | 25 | Re-articulation dip |
| `dip_level` | 0–1 | 0.2 | |
| `dip_vowel` | 0–1, null | null | The dip's vowel |
| `compress` | 0/1 | 1 | Fast-note rule (§6.8) |

### 7.7 `vibrato`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `depth` | 0.2–1.2 st | 0.2 | Peak deviation; 0.2 is the floor, 0.35 a sung lead |
| `rate` | 1.5–24 Hz | 6 | |
| `delay` | 0–2000 | 0 | At the floor before this |
| `fade` | 0–2000 | 0 | Linear rise to `depth` |
| `modwheel` | 0–1 st | 0.3 | Extra depth at CC1 = 127 |
| `lock` | 0/1 | 0 | A chord's monks share one LFO, so its intervals hold |

### 7.8 `voice`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `size` | 0–1 | 0.5 | Formant scale 0.75–1.25 |
| `pitch_track` | −0.2..+0.2 per octave | 0 | Smaller voice when higher |
| `formant1`–`formant3` | 0–2 | 1 | That formant's frequencies × factor; 0 silences it. The size still scales all three |

### 7.9 `ensemble`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `unison` | 1–10 | 1 | Voices per monk |
| `detune` | 0–50 cents | 0 | |
| `spread` | 0–1 | 0 | Voice-size spread across the unison voices |

### 7.10 `dyn`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `velocity` | 0–2 | 1 | Level = (*v*/127)^`velocity` |
| `burst_velocity` | 0–1 | 0.5 | How much the burst grows with velocity |
| `gain` | 0–4 | 1 | The profile's level factor, set by measurement (§15) |
| `even` | 0–1 | 0 | Reserved: even out high-register loudness jumps |

CC7, CC11 and the channel `gain` scale the level on the GM curve (squared).
The sustain pedal defers note-offs.

## 8. Phrasing rules

1. **Connected notes** stay on one monk. A note that starts while the line's
   previous note is held, or within `phrase.gap` after it ended, goes to that
   monk. Notes that start within 30 ms of each other are a chord and go to
   other monks.
2. **Transition type** for a connected note: in *auto*, legato if it overlaps
   by at least `phrase.overlap`, otherwise re-articulated. *legato*,
   *rearticulate* and *detached* force a type. A repeated pitch is always
   re-articulated, and a note that isn't connected starts new.
3. **Legato**: no new onset, burst or scoop. The pitch slides on the DSP
   glide (or through the bend in mode 1), the vowel moves to the new nucleus,
   and the level carries on.
4. **Re-articulation**: the dip, then the new onset. The pitch jumps at the
   bottom of the dip.
5. **Overlaps without durations** (live input): an overlapping note is
   legato if exactly one note is held on that monk's line and the mode
   allows legato. Otherwise it is a chord note.
6. **Voice stealing**: a stolen monk makes the transition its profile
   would make for a connected note.
7. **Sustain pedal**: note-offs wait for the pedal to lift, while the body
   decay keeps running.
8. **`allnotesoff`**: every monk fades out in 10 ms.
9. **Program change**: the new profile applies to notes that start later.

## 9. Choir

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `choir.voice_var` | 0–0.1 | 0.03 | Monk *k* sings with voice size ± this (alternating) |
| `choir.vibrato_var` | 0–0.2 | 0.08 | Vibrato rate × (1 ± this), spread across the monks |
| `choir.seed` | 0/1 | 1 | Each monk gets its own vibrato seed |
| `choir.pan` | 0–1 | 0.5 | Stereo spread, monk 1 left to monk *K* right (equal-power) |

Own seeds make a chord's intervals swing by up to ~75 cents (§16). A profile
that must hold its chords in tune sets `vibrato.lock`.

## 10. The mouth

The singing frame follows the sung vowel. The mouth shows **closed lips**
(sheet column 0, same row) in these cases:

- during the onset when `onset.lips` is set
- for the last 60 % of the release when `ending.lips` is set
- during a dip whose vowel is below 0.1
- whenever the level falls below `mouth.closed_below` (0–1, default 0.15)
  in a dip or an ending

## 11. Space

One `MonkDelay` per helper on the choir mix, with each synth's own echo at
0: `space.echo` (0–1, default 0; most profiles have no echo), `space.echo_time` (0–1, default 0.5),
`space.echo_feedback` (0–0.95, default 0.5).

## 12. Interface

Protocol 1 (ARCHITECTURE.md) carries the profile:

- `set articulator 1` switches to profile mode; the router always sends it.
- Keys between `set profile.begin 1` and `set profile.apply 1` are staged
  and take effect together for later notes; `profile.reset 1` restores the
  defaults first.
- `on` takes the note's length.
- `next <key> <value>` overrides a key for the next note only.

The channel keys sit outside profiles:

| Key | Range | Meaning |
| --- | --- | --- |
| `exaggerate` | 0–2 | Exaggeration (§1) |
| `range.shift` | −48..+48 st | The router's fit (§7.1) |
| `choir.*`, `space.*` | §9, §11 | |
| `mouth.closed_below` | 0–1 | §10 |
| `gain`, `volume` | as protocol 0 | Channel level |

## 13. Profile data

`profiles/imitation.json` holds the syllable table, the profiles (with
`extends`) and the program map. midis2jam2's `ImitationProfiles.kt` and
`tools/profiles/expand.py` expand it the same way, and a test compares the
two.

```json
{
  "version": 1,
  "syllables": {
    "onsets": {
      "b":  {"onset": {"time": 40, "attack": 5, "lips": 1}, "colour": {"vowel": 0.0}},
      "d":  {"onset": {"time": 50, "attack": 3}, "colour": {"vowel": 0.7}}
    },
    "vowels": {"u": 0.0, "oo": 0.12, "o": 0.25, "aw": 0.38, "a": 0.5, "ae": 0.62, "e": 0.75, "ih": 0.88, "i": 1.0},
    "endings": {
      "m":  {"ending": {"vowel": 0.0, "release": 80, "lips": 1}},
      "ng": {"ending": {"vowel": 0.15, "release": 120}}
    }
  },
  "profiles": {
    "default": {"syllable": "d-a", "phrase": {"mode": 0}},
    "bass.finger": {
      "extends": "default", "syllable": "d-oo-m",
      "nucleus": {"pitch_track": 0},
      "body": {"decay": 300, "sustain": 0.3}, "ending": {"release": 50},
      "phrase": {"mode": 3}, "voice": {"size": 0.35}
    }
  },
  "map": [
    {"programs": [33], "profile": "bass.finger"},
    {"bank": 1024, "programs": [29], "profile": "guitar.overdrive"}
  ]
}
```

- **Syllable grammar**: `onset-nucleus[-ending]`. The nucleus may be two
  vowels joined by `>`, and the second becomes `body.vowel` ("d-i>e"). A
  missing onset means a soft start. Expansion order: the `extends` chain,
  then the syllable, then the profile's own numbers. A syllable sets every
  key that syllables control, with unnamed ones at their defaults, so a parent profile's syllable never leaks into a child's. So a
  child's syllable also resets values its parent set inside that set of keys
  (as with `sax.tenor`, §16).
- **Onset tokens** set attack, lips, step time and dip. Their vowel is only
  `colour`, which the expander ignores (§16). Onsets: `b`, `p`, `d`, `t`,
  `g`, `k`, `n`, `m`, `ny`, `w`, `y`, `l`, `h`, `j`/`ch`, `f`. Endings: none,
  `m`, `n`, `ng`, `t`/`k`, `w`, `y`.
- **Map**: `bank` is MSB × 128 + LSB, as in the `program` line. Entries with
  a bank match first, then plain program entries, then a family default by
  program range, then `default`. Rhythm channels are never mapped: drums stay with Gervill. The
  panel can override the profile per channel.

## 14. Family defaults

GM programs are 1-based here (MIDI data is 0-based). For every family:
written pitch with high parts folded (§7.1), breath 0.75 unless given,
no echo, the moderate velocity curve, steady onsets and DSP glide 0.5 for
legato. **Tuned** rows have been tuned against Gervill (§15) and match
`imitation.json`. The others are first-guess designs; `imitation.json` is
what actually plays, and a program it has no profile for takes its family
default or `default` (§13).

| Family (programs) | Syllable | Onset | Body | Ending | Phrase | Vibrato | Voice |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Piano (1–8), tuned** | d-i>e | crisp | decay 900, sustain 0, track 0.7, drift 600 | release 120, no "ng" | detached | straight | 0.6 |
| Chromatic perc. (9–16) | t-i (glock, celesta, music box); b-o (marimba, xylophone); d-o>u-ng (bells) | crisp | decay 450 / 200 / 2500, sustain 0 | –, 40 | detached | straight; vibraphone tremolo 5 Hz | 1.0 / 0.45 / 0.5 |
| Organ (17–24) | u (drawbar), d-u (percussive), a (rock: tremolo 6.5 Hz), o (church, unison 3), e (reed, accordion), w-a (harmonica) | attack 5 | sustain 1 | release 15 | legato | straight | 0.5 |
| Guitar, clean (25–28) | d-o-ng (nylon), d-a-ng (steel, clean), d-u-m (jazz) | crisp | decay 1300, sustain 0.1, drift to 0.4 | ng, 140 | auto, glide 0.15 | straight | 0.5 |
| Guitar, muted (29) | d-u | crisp | max 60, decay 50 | –, 20 | rearticulate | straight | 0.4 |
| Guitar, overdrive/distortion (30–31) | ny-a-w | scoop −1/90, attack 15 | decay 1500, sustain 0.75, breath 0.6 | w, fall −0.7/300 | legato, glide 0.15 | lead, delay 450; distortion 24 Hz growl, unison 2 | 0.45 |
| Guitar harmonics (32) | t-i-ng | crisp | decay 1500, sustain 0 | ng | detached | straight | 0.9 |
| Bass (33–40); **finger tuned** | d-oo-m (finger, no vowel tracking), d-o-m (pick), w-u (fretless, legato), b-a (slap, max 80) | crisp | decay 300, sustain 0.3 | m, 50 | detached; fretless legato | straight | 0.35 |
| Strings, solo (41–44); **violins tuned** | violin, viola (41–42): `lead.singer` "a"; `strings.violin` n-i without glides; m-o (cello), m-u (contrabass) | attack 120 (cello 150; singer 40) | sustain 1, breath 0.5 | release 200 (singer 120) | singer glides on slurs, cello legato | lead, 6.5 Hz, delay 300, fade 400 | 0.7 / 0.6 / 0.3 / 0.1 |
| Tremolo strings (45) | n-a | attack 60 | tremolo 0.6 at 12 Hz | release 150 | legato | straight | 0.6 |
| Pizzicato (46), harp (47) | p-i (max 80); d-i-ng (decay 1500) | crisp | decay 120 / 1500, sustain 0 | – | detached | straight | 0.7 |
| Timpani (48) | b-o-m | crisp, scoop +2/40 | decay 600 | m | detached | straight | 0.2 |
| Ensembles (49–52); **49–50 tuned** | 49–50: `lead.singer`; 51–52 synth strings: a (`strings.ensemble`) | attack 300 | sustain 1 | release 500 | legato | straight | 0.5, unison 4, 12 ct |
| Choir aahs (53), voice oohs (54), synth voice (55) | a; u; u>a | attack 150 | sustain 1 | release 300 | legato | lead | 0.5, unison 3 |
| Orchestra hit (56) | b-a | crisp, peak 1.3 | decay 300, sustain 0 | – | detached | straight | 0.5, unison 6 |
| **Trumpet (57), tuned** | t-a | scoop −0.4/40, attack 6, peak 1.15, burst 0.6/30 | decay 150, sustain 0.8 | release 100 | rearticulate | lead, delay 350 | 0.6 |
| Trombone (58) | b-a | scoop −1.5/120, attack 25 | sustain 1 | o, 120 | auto, glide 0.5 | lead, delay 400 | 0.35 |
| Tuba (59) | b-o-m | attack 30 | sustain 0.9 | m, 100 | rearticulate | straight | 0.0 |
| Muted trumpet (60) | w-a-w | onset time 180 | breath 0.6 | w, 200 | rearticulate | lead | 0.6 |
| French horn (61) | d-o (no profile of its own: it plays `brass.section`) | attack 40 | sustain 1 | release 150 | legato | lead | 0.4 |
| Brass section, synth brass (62–64) | b-a; b-a-w | attack 20 | sustain 0.85 | release 120 | rearticulate | straight | 0.5, unison 4, 8 ct |
| Saxes (65–68); **tenor tuned** | d-u>a (soprano, alto), d-u>o (tenor, breath 0.6), b-u>o (baritone) | scoop −0.8/100, attack 20 | drift over 500 | o, 120 | legato | lead, delay 350 | 0.6 / 0.55 / 0.4 / 0.2 |
| Oboe, English horn (69–70) | n-i; n-e | attack 30 | breath 0.5 | release 100 | legato | lead, delay 250 | 0.7 / 0.6 |
| Bassoon (71) | b-o | attack 30 | breath 0.5 | release 100 | legato | straight | 0.3 |
| Clarinet (72) | d-oo | attack 25 | | release 100 | legato | straight | 0.45 |
| **Flute (73–80), tuned** | h-u (one `flute` profile for every pipe) | attack 40 | sustain 1, breath 0.3, F3 off, `dyn.gain` 1.8 | release 100 | auto, slurs legato on glide 0.1, dip 0.4 | lead, delay 250, fade 300 | 0.75 |
| Synth lead (81–88) | b-o (square), ny-a (saw), u (calliope), t-u (chiff), ny-a-w (charang), a (voice, fifths), b-a (bass + lead) | attack 10 | sustain 1 | release 60 | legato, glide 0.15 | straight | 0.5 |
| Synth pad (89–96) | u>a swells | attack 600 | drift over 2000 | release 800 | legato | straight | 0.5, unison 5, 15 ct |
| Synth FX (97–104) | pad-like; d-i-ng for crystal (99) | | | | | | |
| Ethnic (105–112) | ny-i-ng (sitar), p-i-ng (banjo), t-e-ng (shamisen), d-i-ng (koto, kalimba), a (bagpipe, unison 2), n-i (fiddle, shanai) | | | | | | |
| Percussive (113–120) | t-i (tinkle bell), k-o (agogo), b-o-ng (steel drums), t-o (woodblock), d-o-m (taiko), d-u-m (melodic tom, fall −3), b-u (synth drum, fall −5), h-a reversed (reverse cymbal) | | | | | | |
| Sound effects (121–128) | novelty only (breath h, bird w-i with 24 Hz vibrato, telephone i with tremolo, helicopter b-u with tremolo) | | | | | | |
| Drums (rhythm channels) | not sung: they stay with Gervill | | | | | | |

## 15. Tuning method

1. Write the family's test phrases as MIDI (scale, repeated notes, legato
   line, fast run, chord, long notes, and a short band piece), render them
   with Gervill and with the real articulator, and **measure first**: level,
   spectrum against Gervill's, onset and ending flares, decay, fold. Write
   the numbers to `measure/measurements.md` in the family's folder.
2. **Set the level by measurement**. Match the profile's integrated
   loudness (ITU-R BS.1770, gated) to Gervill's part at the live balance,
   through `dyn.gain`. Never ask the ear about loudness.
3. Fix what the measurement shows with existing keys first. A new key needs
   a helper change (additive to protocol 1, ARCHITECTURE.md), and a DSP
   change must be an add-only addition, since the macOS build shares `DSP/`.
4. Ask the user's ear (a listening set, `tools/listening/`) only where a
   choice of sound is left: which of a few candidates sounds most like the
   instrument, and whether anything glitches. Loudness-match the clips.
5. Fold the pick into `profiles/imitation.json`, and check that
   `DelayLamaProfilesTest` still passes (run it with `--rerun` after a
   JSON-only change).

The tools to copy are in `renders/phase4c/piano/`: `piano_phrases.py`
(phrases, MIDI writer, Gervill render, script builder),
`measure_4c_piano.py` and `make_4c_piano.py`. `pipe_phrases.py` and
`brass_phrases.py` show how other families reuse them, adding the router's
`range.shift`.

## 16. What the DSP means for profiles

### How the DSP glitches

These hold for every family, so check new profiles against them.

- **Any vowel move at a note's start is heard as a glitch**: a "laser",
  a "pew" or a high pitch, whether it moves brighter or darker, fast or
  slow. The formants are narrow and equally strong, so the ear follows one
  as a pitch. On low notes each grain is a separate formant ping. On high
  notes, the harmonic that the moving colour crosses flares by up to +24 dB.
  A masking attack, wider formants and "only after a rest" did not help
  (the experiment keys of §7.2). Keep onsets steady and make consonants from attack, dip, lips
  and scoop.
- **Ending vowel moves do the same at the end**: the "ng" sweep lifts a
  harmonic 24–43 dB as a note fades, heard as a high pitch. Avoid
  closing-vowel moves on ringing notes.
- **High notes move in steps.** The grain period is whole samples, so above
  about sung C5 pitch moves in 30–50 cent steps (17 at A4). Vibrato and
  glides become staircases there, which is why violins glitched at their
  written F5–E6 and why high parts fold down (§7.1).
- **F3 makes high notes buzz or whistle.** The third formant (2.2–2.9 kHz,
  as loud as F1 and F2) lifts whichever harmonic meets it. `voice.formant3`
  0 fixed the flute; 0.6 fills a sax's 800–1600 Hz hole.
- **The breath partials ring on a harmonic** (3.8 and 4.95 kHz; trumpet A4's
  11th harmonic stands +18 dB over its neighbours). Lower `body.breath` to
  quiet them. A possible DSP addition, if breath 0.3 sounds too dry, is a
  scale for the partials' frequency.
- **The vibrato floor detunes chords.** Each monk wobbles ±0.2 st on its own
  LFO, so a chord's intervals swing by ~75 cents. `vibrato.lock` holds them,
  but in a band the piano sounds better with each monk's own wobble.
- **A drifting vowel swings loudness by 5–10 dB** as formants cross
  harmonics. A steady vowel stays within 2–3 dB.
- **Vowel tracking darkens low notes.** `nucleus.pitch_track` 0.05 per
  octave turned the bass's "oo" into "u" and lost its "doo", so the bass
  has it at 0. Check it on other low instruments.
- **Choir size**: four monks steal pedal-held notes in piano arpeggios,
  starting with the bass (the pedal rule comes before "never the lowest").

### The tuned families

| Family | Profile | Known issues |
| --- | --- | --- |
| Piano (GM 1–8) | `piano` "d-i>e", 900 ms decay, own wobble, no "ng" ending | A longer decay is muddy, and locked chords sound detuned |
| Pipes (GM 73–80) | `flute`: F3 off, breath 0.3, slurs legato on glide 0.1, `dyn.gain` 1.8 | Slow slurs would rather re-articulate; kept legato |
| Trumpet (GM 57) | `trumpet`; no high-pitch ring heard | One glitch in a band clip, accepted. A lead whose median is above C5 (one a tone above the test line) folds an octave down; a per-profile `range.high` of about 76 would keep it as written (untested) |
| Tenor sax (GM 67) | `sax.tenor` | Its syllable resets the alto's attack 20, release 120 and "o" ending (§13); kept that way |
| Violins, string ensembles (GM 41–42, 49–50) | `lead.singer` on "ah", folded; it beat the violin imitation, and `strings.violin` stays for picking per channel | None heard |
| Finger bass (GM 34) | `bass.finger` "d-oo-m", no vowel tracking | None heard |

### The other families

- **Trombone, tuba and horn** measure much brighter than Gervill (energy
  above 1.5 kHz / spectral centroid, Gervill against the monk): trombone
  -9.0 dB / 948 Hz against -4.8 / 1612, tuba -21.8 / 415 against -5.4 / 967,
  horn -21.9 / 430 against -6.4 / 1561. On held notes, F3 off with breath
  0.3 matches the tuba, F3 off matches the trombone, and an "o" with F3 off
  and breath 0.3 comes nearest the horn. The horn has no profile of its
  own and plays `brass.section`.
- **Fast runs**: DSP glide 0.5 smears 110 ms notes.
- **Level**: before tuning, monks came out 2.6 dB (piano) to 5.9 dB (flute)
  under Gervill, and F3 off takes another 4–5 dB, so an untuned family's
  level is not matched to the band until its `dyn.gain` is set by
  measurement (§15).
