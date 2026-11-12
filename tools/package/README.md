# Windows package

`make_package.ps1` builds the Windows package: one folder, zipped, that runs
without this source tree. `check_package.ps1` checks the result without
touching your desktop.

```powershell
.\tools\package\make_package.ps1       # builds midis2jam2, collects, zips
.\tools\package\check_package.ps1      # unzips the newest zip and checks it
```

You get `dist\DelayLamaEverything\` and
`dist\DelayLamaEverything-<date>-windows-x64.zip`: about 190 MB without the
bundle, about 550 MB with the current one (its soundfont is 420 MB).
`dist/` is git-ignored.

Build the Delay Lama exes first (see `CLAUDE.md`), or pass
`-BuildDelayLama`.

## What the script does

1. Builds midis2jam2's app image with `:app:createDistributable`, from
   `external\midis2jam2` as it is checked out, with `JAVA_HOME` set to JDK 21
   and `ANDROID_HOME` set. The image is `midis2jam2.exe`, `app\` (the jars)
   and `runtime\`, a JDK 21 runtime with every module (`includeAllModules`
   in `app/build.gradle.kts`).
2. Adds `runtime\bin\java.exe` and `javaw.exe` from the same JDK, since
   recording starts its renderer with them. It stops if the runtime wasn't
   made from that JDK.
3. Copies `DelayLamaVoice.exe`, `DelayLamaStandalone.exe` and all of
   `Resources\` from `external\delalalalay-lama\Windows\build\Release\`. A
   locked exe is retried for a minute.
4. Copies `profiles\imitation.json` and the licenses into `licenses\`
   (midis2jam2 GPL-3.0 and its third-party notices, delalalalay-lama MIT,
   MonkSynth MIT). Writes `README.txt` and `NOTICE.txt` from
   `package-README.txt` and `package-NOTICE.txt`, filling in the commits.
5. Writes `source\midis2jam2-delay-lama.patch`: every change in the
   midis2jam2 checkout against upstream (`git merge-base HEAD origin/master`),
   committed or not, new files included. `NOTICE.txt` names the upstream
   commit, so the two together are the GPL source.
6. Adds the bundle (`bundle\`, or `-Bundle <folder>`): `soundfonts\`,
   `backgrounds\` and `midi\` go next to `midis2jam2.exe`, its `licenses\`
   into the package's, its `NOTICE.txt` onto the package's, and
   `package-README-bundle.txt` onto the README. A bundle without a
   `NOTICE.txt` is refused. [bundle/README.md](../../bundle/README.md) says
   what the app does with it.
7. Zips the folder, with `DelayLamaEverything\` at the zip's top.

midis2jam2 finds the three Delay Lama files next to `midis2jam2.exe`: the
launcher sets `jpackage.app-path`, and `DelayLamaInstall` turns it into the
app folder the locators try first, after any paths set in the panel
(catalogue entry `delaylama.package.locate`).

## Options

| Option | Default | What it does |
| --- | --- | --- |
| `-Version` | today's date | the zip's name part |
| `-OutDir` | `dist` | where the folder and zip go |
| `-Jdk` | `C:\Program Files\Java\jdk-21` | builds midis2jam2 and supplies `java.exe` |
| `-AndroidSdk` | `%LOCALAPPDATA%\Android\Sdk` | Gradle needs it |
| `-SkipBuild` | off | reuses the app image already built |
| `-BuildDelayLama` | off | builds delalalalay-lama with CMake first |
| `-NoZip` | off | stops after the folder |
| `-Bundle` | `bundle` | the soundfonts, cube maps and songs to ship |
| `-NoBundle` | off | ships without them |

## The check

`check_package.ps1 [-Zip <zip>] [-Script <voice script>] [-Keep]` unzips to
a temp folder. Then, working from a folder outside the package, it:

- starts `midis2jam2.exe`, waits for the
  `Delay Lama: app folder ...; helper ..., standalone ..., profiles ...` log
  line and checks the three paths are the package's own, then stops it. The
  launcher window shows for a few seconds; nothing is clicked or typed.
  Paths set in the panel's options override the package's and fail this
  check.
- if the package ships a bundle, checks that `NOTICE.txt` covers it and
  that the `Delay Lama: package bundle in ...` log line names the package
  folder, each soundfont and each complete cube map. Starting the launcher
  applies the bundle to this Windows user's settings, as any first start
  would, so on a machine that already has a soundfont and background set
  nothing visible changes.
- renders `external\delalalalay-lama\Tests\voice_scripts\chord.txt` with
  the packaged `DelayLamaVoice.exe --render` and checks the WAV.

The check can't play a file with the monks, try Add Delay Lama or record.
Try those by hand in the unzipped package before you hand a zip out.
