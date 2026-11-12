# Instrument imitation

How Delay Lama imitates each instrument: the articulator in
`DelayLamaVoice.exe` (profile mode) and the data in `profiles/imitation.json`.
§15 is the tuning method, and §16 what the DSP's limits mean for profiles.
Code comments cite these section numbers, so keep them stable.

## 1. The goal

When people "play" an instrument with their voice, they don't hold a vowel.
They shape each note like a syllable: a guitar riff becomes
"nyeow-nyeow-dang", a bass line "dum dum doon", a flute "hoo-too-hoo". The
imitation lives in how each note **starts**, **moves** and **ends**, in the
voice's register and vibrato, and in how notes join. Since the monk's mouth
follows the vowel, the monks also look like they are imitating.

Profiles aim to sound like a good a cappella singer. An **exaggeration** amount
(0–2, default 1, one value for all channels) scales the expressive moves.

## 2. The palette

The DSP facts that matter for imitation (`external/delalalalay-lama/DSP/`).
The voice sounds like singing from sounding C2 to C5; outside that range it
still works for imitation.

| Parameter | Range | What it does | For the articulator |
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

**What it can't do**: no unvoiced sound (no "t", "k" or "s" noise), no nasal
murmur as such, only three formants, one note per synth. Consonants are
**suggested** by a level dip, the attack, closed lips and a pitch scoop. A noise
layer sounded worse than pure Delay Lama, and onset vowel moves glitch (§16).

## 3. How people imitate instruments

Imitators reproduce a sound's **loudness envelope, tail length, pitch contour
and brightness**, and simplify the attack
([Lemaitre et al.](https://hal.archives-ouvertes.fr/hal-01256126);
[Delgado et al. 2020](https://comma.eecs.qmul.ac.uk/assets/pdf/delgado_timbre_2020.pdf)),
so profiles get those right in that order. A cappella syllables follow their
role ([Bauer](https://journals.library.columbia.edu/index.php/currentmusicology/article/download/4828/2177/8416)):
soft onsets (d, l, n, w) for legato, hard ones (t, k, p, b) for accents, nasal
endings (m, n, ng) for ringing notes, stop endings for damped ones, brighter
vowels for higher and harder notes, "dum" for bass, "wah"/"bow" for distorted
guitar, and a dark vowel with a big voice for a tuba.

## 4. The model

A **profile** is data. The **articulator** applies the profile of the
channel's current program to every note, per monk.

- Each note runs through **onset → nucleus → body → ending**. Consecutive notes
  on one monk are joined by a **phrasing** transition: new, re-articulated or
  legato.
- Every 1 ms tick it computes each monk's vowel, breath, level, pitch offset,
  vibrato, voice size and mouth, calls the DSP setters, and renders that monk's
  next 1 ms. The DSP envelope and echo are off: notes are shaped through the
  level, and one echo runs on the choir mix.
- A note **snapshots** its profile at the onset, so a profile change applies to
  notes that start later. Ensemble, choir and space keys apply at once.
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

Level **decays** are exponential toward a floor: level(*t*) = *s* + (1 − *s*) ×
e^(−3*t*/*T*). Releases use the same form toward 0. A note ends (the DSP
note-off) 40 dB below where its ending started, or at 1.5 × the release time.

## 6. Per-note behaviour

For a note with written pitch *n*, velocity *v* and sounding pitch
*n*s = *n* + `range.shift`:

1. **Pitch**: the DSP note is *n*s + 12. The pitch offset combines the file's
   bend (pitch bend is pitch bend, not the standalone's vowel wheel), the onset
   scoop and the ending fall, plus a drawn glide when `phrase.glide_mode` is 1.
   It goes out as one bend, clamped to ±12 st. A legato note sets the DSP glide
   to `phrase.glide` just before it starts; new and re-articulated notes set
   the glide to 0.
2. **Nucleus vowel** *V* = `nucleus.vowel` + `nucleus.pitch_track` ×
   (*n*s − 60) / 12 + `nucleus.velocity_track` × (*v* − 64) / 63, clamped to
   0–1.
3. **Vowel**: the note starts on *V* (onsets are steady, §16). A profile can
   set `onset.vowel` to move from it over `onset.time`. The vowel then drifts
   toward `body.vowel` (`exp`, `body.vowel_time`). In the ending it moves
   toward `ending.vowel` over `ending.vowel_time` (`ease`). On a legato note it
   moves from the previous vowel over `phrase.legato_vowel_time`.
4. **Level**: a re-articulated note first holds `phrase.dip_level` for
   `phrase.dip_time`. The attack rises linearly over `onset.attack` to
   `onset.peak`; 0 is crisp, with the level preset before the note-on. Then
   comes an exponential decay toward `body.sustain` × peak over `body.decay`
   (scaled by `body.decay_track` per octave above sounding C4), times the
   tremolo, then the release. A legato note keeps the previous level and moves
   to the body level over 40 ms.
5. **Breath**: `onset.burst` falls to `body.breath` over `onset.burst_time`.
   During the release the breath is `ending.breath` if set. The burst grows
   with velocity by `dyn.burst_velocity`.
6. **Vibrato**: the floor until `vibrato.delay`, then a linear rise to
   `vibrato.depth` over `vibrato.fade`, plus `vibrato.modwheel` × CC1/127.
7. **Exaggeration** *x* (0–2) scales the distance from the plain value of the
   vowels, the scoop and fall, the vibrato above the floor, the burst, the dip
   depth and the tracking amounts.
8. **Fast notes**: with `phrase.compress` on, the onset, scoop, attack, burst
   and dip times are multiplied by *k* = clamp(*d* / (3 × *T*), 0.25, 1). *T*
   is the longest of those times and *d* the note's length (from `on`, or else
   the last inter-onset interval).

## 7. Profile parameters

JSON nests the keys by section, and `set` keys are `section.param`. "null"
means "follow the nucleus" and is sent as −1. The full list with ranges and
defaults is `Windows/voice_profile_keys.inc` in delalalalay-lama.

### 7.1 `range`

| Key | Range | Default | Meaning |
| --- | --- | --- | --- |
| `octave` | −3..+3 | 0 | Shift from the written pitch |
| `fit` | 0 off, 1 octaves, 2 down | 2 | Router-side shift of the whole channel by octaves. 2: down while the channel's median is above `high`; it never shifts up, so a line keeps its shape. 1: the median nearest `target` |
| `target` | sounding note | 57 | For `fit` 1 |
| `low`, `high` | sounding notes | 36, 72 | `high` (C5) is `fit` 2's ceiling; both bound `fold` |
| `fold` | 0/1 | 0 | Fold single notes outside `low`..`high`. Off, because it breaks a line's shape |

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
| `mask`, `bandwidth`, `after_rest` | 0–3, 1–8, 0–5000 | 0, 1, 0 | Experiment keys, left off because none fixed the onset glitch or made a consonant: a masking attack, wider formants during an onset move, a move only after a rest |

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
3. **Legato**: no new onset, burst or scoop. The pitch slides on the DSP glide
   (or through the bend in mode 1), the vowel moves to the new nucleus, and the
   level carries on.
4. **Re-articulation**: the dip, then the new onset. The pitch jumps at the
   bottom of the dip.
5. **Overlaps without durations** (live input): an overlapping note is legato
   if exactly one note is held on that monk's line and the mode allows legato.
   Otherwise it is a chord note.
6. **Voice stealing**: a stolen monk makes the transition its profile would
   make for a connected note.
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
(sheet column 0, same row):

- during the onset when `onset.lips` is set;
- for the last 60 % of the release when `ending.lips` is set;
- during a dip whose vowel is below 0.1;
- whenever the level falls below `mouth.closed_below` (0–1, default 0.15) in
  a dip or an ending.

## 11. Space

One `MonkDelay` per helper runs on the choir mix, with each synth's own echo
at 0. Keys: `space.echo` (0–1, default 0; most profiles have no echo),
`space.echo_time` (0–1, default 0.5), `space.echo_feedback` (0–0.95, default
0.5).

## 12. Interface

Protocol 1 ([ARCHITECTURE.md](ARCHITECTURE.md#pipe-protocol-version-1))
carries the profile:

- `set articulator 1` switches to profile mode; the router always sends it.
- Keys between `set profile.begin 1` and `set profile.apply 1` are staged and
  take effect together for later notes; `profile.reset 1` restores the
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

**Syllable grammar**: `onset-nucleus[-ending]`. The nucleus may be two vowels
joined by `>`, and the second becomes `body.vowel` ("d-i>e"). A missing onset
means a soft start. Expansion order is the `extends` chain, then the syllable,
then the profile's own numbers. A syllable sets every key that syllables
control, with unnamed ones at their defaults, so a parent profile's syllable
never leaks into a child's. It follows that a child's syllable also resets
values its parent set among those keys (as with `sax.tenor`, §16).

**Tokens**: onset tokens set attack, lips, step time and dip. Their vowel is
only `colour`, which the expander ignores (§16). Onsets: `b`, `p`, `d`, `t`,
`g`, `k`, `n`, `m`, `ny`, `w`, `y`, `l`, `h`, `j`/`ch`, `f`. Endings: none,
`m`, `n`, `ng`, `t`/`k`, `w`, `y`.

**Map**: programs in the JSON are 0-based, as in MIDI data. `bank` is MSB ×
128 + LSB, as in the `program` line. Entries with a bank match first, then
plain program entries, then `default`. Rhythm channels are never mapped: drums
stay with Gervill. The panel can override the profile per channel.

§14 lists every profile with the programs the map sends to it.

## 14. The profiles

Every profile in `imitation.json`, with the programs the map (§13) sends to
it. Programs are 1-based here. Unless a row says otherwise, a profile sings
at written pitch with high parts folded (§7.1), breath 0.75, no echo, the
moderate velocity curve, a steady onset and DSP glide 0.5 for legato.

The row gives a profile's own values; the JSON has the rest. A profile that
extends another keeps its parent's numbers, except that its own syllable
resets the values syllables control (§13). **Tuned** profiles have been tuned
against Gervill (§15, §16); the others are first guesses.

| Profile | Programs | Syllable | Notes join | Own values |
| --- | --- | --- | --- | --- |
| `default` | 47–48, 56, 97–128 | d-a | auto | Every program with no entry of its own |
| `piano`, **tuned** | 1–8 | d-i>e | detached | Crisp start, decay 900 to silence (track 0.7), vowel drift over 600, release 120, size 0.6 |
| `chromatic.bells` | 9–11, 15 | t-i | detached | Extends `piano`: decay 450, release 40, size 1.0 |
| `chromatic.mallets` | 12–14, 16 | b-o | detached | Extends `piano`: decay 200, release 40, size 0.45 |
| `organ` | 17, 20–21, 23–24 | u | legato | Attack 5, full sustain, release 15, size 0.5 |
| `organ.rock` | 18–19 | a | legato | Extends `organ`: tremolo 0.3 at 6.5 Hz |
| `organ.church` | none (pick it in the panel) | o | legato | Extends `organ`: unison 3, 8 ct |
| `organ.reed` | 22 | e | legato | Extends `organ`: unison 2, 10 ct |
| `guitar.clean` | 26, 28, 32 | d-a-ng | auto, glide 0.15 | Decay 1300 to 0.1, vowel drift to 0.4 over 800, release 140, size 0.5 |
| `guitar.nylon` | 25 | d-o-ng | auto, glide 0.15 | Extends `guitar.clean` |
| `guitar.jazz` | 27 | d-u-m | auto, glide 0.15 | Extends `guitar.clean` |
| `guitar.muted` | 29 | d-u | rearticulate | At most 60 long, decay 50 to silence, release 20, size 0.4 |
| `guitar.overdrive` | 30 | ny-a-w | legato, glide 0.15 | Scoop −1 st over 90, decay 1500 to 0.75, breath 0.6, fall −0.7 over 300, vibrato at 6 Hz after 450, size 0.45 |
| `guitar.distortion` | 31 | ny-a-w | legato, glide 0.15 | Extends `guitar.overdrive`: vibrato at 24 Hz (a growl), unison 2, 8 ct |
| `bass.finger`, **tuned** | 33–34, 39–40 | d-oo-m | detached | No vowel tracking, decay 300 to 0.3, release 50, size 0.35 |
| `bass.pick` | 35 | d-o-m | detached | Extends `bass.finger` |
| `bass.fretless` | 36 | w-u | legato | Extends `bass.finger` |
| `bass.slap` | 37–38 | b-a | detached | Extends `bass.finger`: at most 80 long |
| `lead.singer`, **tuned** | 41–42, 49–50 | a | auto | Extends `choir.aahs`: a singer on "ah", not an imitation. One voice, attack 40, release 120, size 0.5 |
| `strings.violin` | none (pick it in the panel) | n-ih | detached | Attack 120, full sustain, breath 0.5, release 200, vibrato at 6.5 Hz after 300, size 0.7 |
| `strings.cello` | 43–44 | m-o | legato | Extends `strings.violin`: attack 150, size 0.3 |
| `strings.ensemble` | 45–46, 51–52 | a | legato | Attack 300, full sustain, release 500, unison 4, 12 ct |
| `choir.aahs` | 53 | a | legato | Attack 150, full sustain, release 300, vibrato after 250, unison 3, 10 ct |
| `choir.oohs` | 54–55 | u | legato | Extends `choir.aahs` |
| `trumpet`, **tuned** | 57, 60 | t-a | rearticulate | Scoop −0.4 st over 40, attack 6 to a peak of 1.15, breath burst 0.6 for 30, decay 150 to 0.8, release 100, vibrato after 350, size 0.6 |
| `trombone` | 58 | b-a | auto, glide 0.5 | Scoop −1.5 st over 120, attack 25, full sustain, ends on "o", release 120, vibrato after 400, size 0.35 |
| `tuba` | 59 | b-o-m | rearticulate | Attack 30, sustain 0.9, release 100, size 0 |
| `brass.section` | 61–64 | b-a | rearticulate | Attack 20, sustain 0.85, release 120, unison 4, 8 ct |
| `sax.alto` | 65–66 | d-u>a | legato | Scoop −0.8 st over 100, attack 20, vowel drift over 500, ends on "o", release 120, vibrato after 350, size 0.55 |
| `sax.tenor`, **tuned** | 67–68 | d-u>o | legato | Extends `sax.alto`: breath 0.6, size 0.4 (§16) |
| `clarinet` | 69–72 | d-oo | legato | Attack 25, release 100, size 0.45 |
| `flute`, **tuned** | 73–80 | h-u | auto, glide 0.1, dip 0.4 | Attack 40, full sustain, breath 0.3, third formant off, release 100, vibrato after 250, `dyn.gain` 1.8, size 0.75 |
| `lead.synth` | 81–88 | ny-a | legato, glide 0.15 | Attack 10, full sustain, release 60 |
| `pad` | 89–96 | u>a | legato | Attack 600, vowel drift over 2000, release 800, unison 5, 15 ct |

Times are in ms. Drums (rhythm channels) are not sung: they stay with Gervill.

## 15. Tuning method

1. Write the family's test phrases as MIDI (scale, repeated notes, legato
   line, fast run, chord, long notes, and a short band piece). Render them with
   Gervill and with the real articulator, and **measure first**: level,
   spectrum against Gervill's, onset and ending flares, decay, fold. The
   numbers go to `renders/tuning/<family>/measure/measurements.md`.
2. **Set the level by measurement.** Match the profile's integrated loudness
   (ITU-R BS.1770, gated) to Gervill's part at the live balance, through
   `dyn.gain`. Never ask the ear about loudness.
3. Fix what the measurement shows with existing keys first. A new key needs a
   helper change (additive to protocol 1, see
   [ARCHITECTURE.md](ARCHITECTURE.md#pipe-protocol-version-1)), and a DSP
   change must only add functions, since the macOS build shares `DSP/`.
4. Ask the user's ear (a listening set, `tools/listening/`) only where a choice
   of sound is left: which of a few candidates sounds most like the
   instrument, and whether anything glitches. Loudness-match the clips.
5. Fold the pick into `profiles/imitation.json` and check that
   `DelayLamaProfilesTest` still passes (run it with `--rerun` after a
   JSON-only change).

The tools are in `tools/tuning/` and write to `renders/tuning/<family>/`.
`dl.py` is shared (renders a helper script, reads and writes WAVs, tracks
pitch) and `GervillRender.java` renders the Gervill side. Start from
`tools/tuning/piano/`: `piano_phrases.py` (phrases, MIDI writer, Gervill
render, script builder), `measure_4c_piano.py` (for example
`py tools\tuning\piano\measure_4c_piano.py`) and `make_4c_piano.py`. The
`pipe/` and `brass/` folders show how other families reuse them, adding the
router's `range.shift`.

## 16. What the DSP means for profiles

### How the DSP glitches

These hold for every family, so check new profiles against them.

- **Any vowel move at a note's start is heard as a glitch**: a "laser", a
  "pew" or a high pitch, whether it moves brighter or darker, fast or slow. The
  formants are narrow and equally strong, so the ear follows one as a pitch.
  On low notes each grain is a separate formant ping; on high notes the
  harmonic the moving colour crosses flares by up to +24 dB. The experiment
  keys of §7.2 did not help. Keep onsets steady and make consonants from
  attack, dip, lips and scoop.
- **Ending vowel moves do the same at the end**: the "ng" sweep lifts a
  harmonic 24–43 dB as a note fades, heard as a high pitch. Avoid closing-vowel
  moves on ringing notes.
- **High notes move in steps.** The grain period is whole samples, so above
  about sung C5 pitch moves in 30–50 cent steps (17 at A4). Vibrato and glides
  become staircases there, which is why violins glitched at their written
  F5–E6 and why high parts fold down (§7.1).
- **F3 makes high notes buzz or whistle.** The third formant (2.2–2.9 kHz, as
  loud as F1 and F2) lifts whichever harmonic meets it. `voice.formant3` 0
  fixes the flute; 0.6 fills a sax's 800–1600 Hz hole.
- **The breath partials ring on a harmonic** (3.8 and 4.95 kHz; trumpet A4's
  11th harmonic stands +18 dB over its neighbours). Lower `body.breath` to
  quiet them. If breath 0.3 sounds too dry, a possible DSP addition is a scale
  for the partials' frequency.
- **The vibrato floor detunes chords.** Each monk wobbles ±0.2 st on its own
  LFO, so a chord's intervals swing by ~75 cents. `vibrato.lock` holds them,
  but in a band the piano sounds better with each monk's own wobble.
- **A drifting vowel swings loudness by 5–10 dB** as formants cross harmonics.
  A steady vowel stays within 2–3 dB.
- **Vowel tracking darkens low notes.** `nucleus.pitch_track` 0.05 per octave
  turns the bass's "oo" into "u" and loses its "doo", so the bass has it at 0.
  Check it on other low instruments.
- **Choir size**: four monks steal pedal-held notes in piano arpeggios,
  starting with the bass (the pedal rule comes before "never the lowest").

### The tuned families

| Family | Profile | Known issues |
| --- | --- | --- |
| Piano (GM 1–8) | `piano` "d-i>e", 900 ms decay, own wobble, no "ng" ending | A longer decay is muddy, and locked chords sound detuned |
| Pipes (GM 73–80) | `flute`: F3 off, breath 0.3, slurs legato on glide 0.1, `dyn.gain` 1.8 | Slow slurs would rather re-articulate; kept legato |
| Trumpet (GM 57) | `trumpet`; no high-pitch ring heard | One accepted glitch in a band clip. A lead whose median is above C5 folds an octave down; a per-profile `range.high` of about 76 would keep it as written (untested) |
| Tenor sax (GM 67) | `sax.tenor` | Its syllable resets the alto's attack 20, release 120 and "o" ending (§13); kept that way |
| Violins, string ensembles (GM 41–42, 49–50) | `lead.singer` on "ah", folded; it sounds better than the violin imitation, and `strings.violin` stays for picking per channel | None heard |
| Finger bass (GM 34) | `bass.finger` "d-oo-m", no vowel tracking | None heard |

### The other families

- **Trombone, tuba and horn** measure much brighter than Gervill (energy above
  1.5 kHz / spectral centroid, Gervill against the monk): trombone −9.0 dB /
  948 Hz against −4.8 / 1612, tuba −21.8 / 415 against −5.4 / 967, horn −21.9 /
  430 against −6.4 / 1561. On held notes, F3 off with breath 0.3 matches the
  tuba, F3 off matches the trombone, and an "o" with F3 off and breath 0.3
  comes nearest the horn. The horn has no profile of its own and plays
  `brass.section`.
- **Fast runs**: DSP glide 0.5 smears 110 ms notes.
- **Level**: before tuning, the monks came out 2.6 dB (piano) to 5.9 dB
  (flute) under Gervill, and F3 off takes another 4–5 dB, so an untuned
  family's level is not matched to the band until its `dyn.gain` is set by
  measurement (§15).
