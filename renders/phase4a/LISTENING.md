# Phase 4a palette demo: listening guide

Rendered by `make_palette.py` with `DelayLamaVoice.exe --render` (protocol 0,
one monk, 48 kHz). The curves are drawn by the script at 5 ms steps, since the
helper has no articulator yet. Notes sound an octave below their MIDI number.
Echo is off except in p09.

## p01_vowels.wav

Vowel axis: nine positions, then u-o-a-e-i at four pitches

- 0:00.0  Nine positions 0, .125 ... 1 on note 69 (sounds A3, 220 Hz): u, (ʊ), o, (ɔ), a, (æ), e, (ɪ), i
- 0:08.4  u-o-a-e-i on note 57 (sounds 110 Hz)
- 0:11.7  u-o-a-e-i on note 69 (sounds 220 Hz)
- 0:15.0  u-o-a-e-i on note 81 (sounds 440 Hz)
- 0:18.3  u-o-a-e-i on note 93 (sounds 880 Hz)

## p02_sweeps.wav

Vowel moves drawn at 5 ms steps, note 69 (220 Hz)

- 0:00.0  Slow sweep u -> i (1 s, linear): passes o, a, e on the way
- 0:01.9  Slow sweep i -> u (1 s, linear): ee-eh-ah-oh-oo
- 0:03.9  'yeow' i -> u in 400 ms (ease)
- 0:05.2  'yeow' i -> u in 200 ms (ease)
- 0:06.2  'yeow' i -> u in 100 ms (ease)
- 0:07.2  'yeow' i -> u in 50 ms (ease)
- 0:08.1  'wa' u -> a in 200 ms (ease)
- 0:09.0  'wa' u -> a in 100 ms (ease)
- 0:09.9  'wa' u -> a in 50 ms (ease)
- 0:10.7  'wa' u -> a in 25 ms (ease)
- 0:11.5  Jump u -> i (step): what an unsmoothed change sounds like
- 0:12.5  'ai' a -> i in 150 ms (ease)
- 0:13.6  'ya' i -> a in 80 ms (exp)

## p03_breath.wav

Breath (aspiration) levels and bursts

- 0:00.0  Breath 0, .25, .5 (default), .75, 1 on vowel a, note 69 (220 Hz)
- 0:05.0  Breath 1 on notes 45, 69, 93 (55, 220, 880 Hz): the pings follow the pitch
- 0:08.3  Onset bursts on 'a': none, then breath 1 -> 0.3 over 15, 40, 100 ms

## p04_voice.wav

Voice size (formant scale 0.75-1.25)

- 0:00.0  Voice 0, .25, .5 (default), .75, 1 on vowel a, note 69 (220 Hz)
- 0:05.0  'Tuba': voice 0, vowel 0.1, note 50 (73 Hz)
- 0:06.2  'Piccolo': voice 1, vowel 1, note 93 (880 Hz)

## p05_range.wav

Range: arpeggios per octave, then one bass riff at four octaves

- 0:00.0  C-E-G-C from note 24 (sounds from 16 Hz)
- 0:01.4  C-E-G-C from note 36 (sounds from 33 Hz)
- 0:02.7  C-E-G-C from note 48 (sounds from 65 Hz)
- 0:04.0  C-E-G-C from note 60 (sounds from 131 Hz)
- 0:05.4  C-E-G-C from note 72 (sounds from 262 Hz)
- 0:06.8  C-E-G-C from note 84 (sounds from 523 Hz)
- 0:08.1  C-E-G-C from note 96 (sounds from 1047 Hz)
- 0:09.4  Note 108 (sounds C7, 2093 Hz)
- 0:10.4  Bass riff 'dum' as written (E1 = note 28): the DSP sounds it at E0, 21 Hz
- 0:13.0  Bass riff 'dum' +1 octave (note 40): sounds E1, 41 Hz
- 0:15.6  Bass riff 'dum' +2 octaves (note 52): sounds E2, 82 Hz
- 0:18.2  Bass riff 'dum' +3 octaves (note 64): sounds E3, 165 Hz

## p06_vibrato.wav

Vibrato: the floor that never stops, depth, rate, delayed vibrato

- 0:00.0  depth 0, rate 0.5: the floor (about ±0.2 st, 5-7 Hz)
- 0:01.9  depth 0, rate 0: floor slowed to about 1.5 Hz
- 0:03.7  depth 0, rate 1: floor at about 24 Hz, a growl
- 0:05.5  depth 0.15 (helper default)
- 0:07.4  depth 0.4
- 0:09.2  depth 1 (±1.2 st)
- 0:11.1  depth 0.3, rate 0.3 (slow, about 3 Hz)
- 0:12.9  depth 0.3, rate 0.7 (fast, about 11 Hz)
- 0:14.8  Delayed vibrato: straight for 400 ms, then fades in to 0.4 over 500 ms

## p07_glide.wav

Legato: the DSP's constant-rate glide vs. glides drawn in a fixed time

- 0:00.0  DSP glide 0.5 (helper default): 23.5 st/s, a fifth takes 0.3 s
- 0:02.5  DSP glide 0.15: 75 st/s
- 0:05.0  Drawn glide, 40 ms (ease), any interval
- 0:07.5  Drawn glide, 90 ms (ease), any interval
- 0:10.1  Drawn glide, 200 ms (ease), any interval
- 0:12.6  Drawn glide, 90 ms (exp), any interval
- 0:15.2  Fast run (110 ms notes) with DSP glide 0.5: the notes smear
- 0:17.3  Same run, drawn 30 ms glides
- 0:19.5  Same run re-articulated ('da-da-da': 20 ms dip to i-ish)

## p08_level.wav

Level shapes: decays, attacks, and repeated notes

- 0:00.0  Pluck: exponential decay, 95% gone in 120 ms
- 0:00.6  Pluck: exponential decay, 400 ms
- 0:01.6  Pluck: exponential decay, 1.2 s
- 0:03.8  Same 1.2 s fall, but linear (the DSP's own ADSR decay)
- 0:05.7  Attack 0 ms
- 0:06.6  Attack 30 ms
- 0:07.6  Attack 120 ms
- 0:08.7  Attack 400 ms
- 0:10.0  Six repeated notes, plain (what the helper does today)
- 0:11.5  Six repeated notes, dip only (30 ms to 20%)
- 0:13.1  Six repeated notes, dip + dark vowel: 'ba-ba'
- 0:14.6  Six repeated notes, dip + bright vowel: 'da-da'
- 0:16.2  Six repeated notes, dip + breath burst: 'ta-ta'

## p09_space.wav

Echo amount and unison on a short phrase

- 0:00.0  Echo amount 0.0
- 0:03.7  Echo amount 0.2
- 0:07.4  Echo amount 0.42 (helper default)
- 0:11.1  Echo amount 0.8 (Delay Lama's Rabten preset)
- 0:14.8  Unison 3 voices, detune 12 cents, spread 0.15, no echo

## g01_gestures.wav

First-guess syllables per family, one note each

- 0:00.0  Bass 'dum' (note 52, sounds E2)
- 0:01.1  Piano 'ding' (note 72, sounds C4)
- 0:02.9  Clean guitar 'dang' (note 67, sounds G3)
- 0:04.7  Overdrive guitar 'nyeow' (note 64, sounds E3)
- 0:06.9  Same 'nyeow' with the vibrato floor at 24 Hz as a growl
- 0:09.1  Trombone 'bwaa' (note 58, sounds Bb2)
- 0:10.8  Trumpet 'taa' with a fall-off (note 70, sounds Bb3)
- 0:12.4  Muted trumpet 'wah' (note 70)
- 0:13.9  Sax 'doo-ah' (note 67, sounds G3)
- 0:15.9  Flute 'hoo' (note 79, sounds G4)
- 0:17.7  Violin 'neee' (note 76, sounds E4)
- 0:19.9  Cello 'mmmooo' (note 60, sounds C3)
- 0:22.3  Organ 'ooo' (note 69): straight on and off, slow floor
- 0:23.8  Glockenspiel 'ting' (note 84, sounds C5)
- 0:25.1  Marimba 'bonk' (note 72, sounds C4)
- 0:26.0  Muted guitar 'chugga': 8 notes, 60 ms each, 125 ms apart (note 52)

## g02_phrases.wav

One melody, four ways; one bass line, two ways

- 0:00.0  Plain: one vowel, no articulation (today's helper)
- 0:04.9  'doo-doo' (soft, re-articulated, dark)
- 0:09.9  Legato 'aah' with 80 ms drawn glides (synth lead / violin slur)
- 0:15.0  Trumpet-like 'taa-daa' (tongued: dip, breath burst, small scoop)
- 0:20.3  Bass line, plain (note 52 = sounds E2)
- 0:22.8  Bass line 'dum dum doon'
