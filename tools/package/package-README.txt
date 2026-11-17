Delay Lama Everything 1.0 for Windows (64-bit), build {{VERSION}}
=================================================================

midis2jam2 with Delay Lama: it plays MIDI files in 3D, and Delay Lama monks
sing the channels you choose, imitating each channel's instrument.

Run
---

1. Unzip this folder anywhere you can write to, for example your Documents.
2. Start midis2jam2.exe. Its programs are not signed, so the first time
   Windows may say "Windows protected your PC": click "More info", then
   "Run anyway".
3. Choose a MIDI file on the home tab. The Delay Lama card shows what will be
   sung: every channel Delay Lama can sing starts switched on, and drums stay
   with midis2jam2. "Choose channels" opens the panel. There you switch
   channels off, set each one's choir size, imitation and level, and choose
   where the monks are shown. Your choices are remembered per file.
4. Press Play. Each sung channel's choir stands on the stage in place of its
   instrument, or in its own always-on-top window if you chose that in the
   panel.
5. While the file plays, the mixer window mutes, solos and sets the level of
   every channel. Each sung channel has a Delay Lama switch that hands it back
   to midis2jam2's own sound at any moment. The mixer also spreads the choirs
   around the stage and turns camera focus on or off. With focus on, the
   channels the camera is close to get louder and the rest get quieter.
6. "Add Delay Lama" on the card or the panel opens DelayLamaStandalone.exe, a
   Delay Lama you play by hand with the mouse or a MIDI keyboard.

midis2jam2 finds DelayLamaVoice.exe, DelayLamaStandalone.exe and
profiles\imitation.json next to midis2jam2.exe. The panel's options can point
to other copies instead.
{{BUNDLE_README}}
Nothing is installed: delete the folder to remove it. midis2jam2 keeps its
settings in your user profile, and the standalone keeps its own in
%APPDATA%\DelayLamaStandalone\settings.ini.

What is in this folder
----------------------

midis2jam2.exe, app\, runtime\   midis2jam2 and the Java runtime it runs on
DelayLamaVoice.exe               the singing helper, one per sung channel
DelayLamaStandalone.exe          Delay Lama to play by hand
Resources\                       AudioNerdz' Delay Lama artwork and manual
profiles\imitation.json          how the monks imitate each instrument
licenses\, NOTICE.txt            licenses and where the source code is
source\                          our changes to midis2jam2, as a patch
soundfonts\                      the bundled soundfont (if any)
backgrounds\                     the bundled cube map (if any)
midi\                            songs to try (if any)

You need Windows 10 or 11, 64-bit, and graphics with OpenGL 3.2: any
graphics card or chip with its driver installed. A virtual machine without 3D
acceleration or a Remote Desktop session won't show the 3D scene.

Known limits
------------

- Some instruments have tuned imitations: piano, flutes and pipes, trumpet,
  tenor sax, violin and viola, string ensembles, and finger bass. The rest
  use first guesses.
- Drums and lyrics are never sung.
- When the monks are shown in windows, closing a monk window silences that
  channel.
- The monks are not in midis2jam2's video recordings.
- The programs are not signed. On Windows 11 with Smart App Control on,
  Windows may block them with no "Run anyway".

Built {{BUILT}}.
