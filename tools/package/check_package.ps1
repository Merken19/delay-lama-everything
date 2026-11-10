<#
.SYNOPSIS
    Checks a Delay Lama Everything package headlessly: unzips it, starts its launcher and reads where it found the
    helper, the standalone and the profiles, then renders a script with the packaged DelayLamaVoice.exe.

.DESCRIPTION
    No input is sent to the launcher: it opens its window, logs the Delay Lama paths
    (DelayLamaPanelModel, "Delay Lama: app folder ...") to stderr, and is stopped. Both programs are started from a
    working directory outside the package, so only the package-relative lookup can find the files.
    The unpacked copy is deleted afterwards unless -Keep or a check failed.

.EXAMPLE
    .\tools\package\check_package.ps1                      # the newest zip in dist\
    .\tools\package\check_package.ps1 -Zip .\dist\DelayLamaEverything-test-windows-x64.zip -Keep
#>
[CmdletBinding()]
param(
    [string]$Zip,
    # A voice script for --render (default: the chord from delalalalay-lama's Tests\voice_scripts).
    [string]$Script,
    # How long to wait for the launcher's log line.
    [int]$TimeoutSeconds = 120,
    [switch]$Keep
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not $Zip) {
    $Zip = (Get-ChildItem (Join-Path $Root 'dist') -Filter 'DelayLamaEverything-*-windows-x64.zip' |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
    if (-not $Zip) { throw 'No package zip in dist\; run make_package.ps1 first' }
}
if (-not $Script) { $Script = Join-Path $Root 'external\delalalalay-lama\Tests\voice_scripts\chord.txt' }
$Zip = (Resolve-Path $Zip).Path
$Script = (Resolve-Path $Script).Path

$work = Join-Path $env:TEMP "dle-package-check-$([guid]::NewGuid().ToString('N').Substring(0, 8))"
$unpacked = Join-Path $work 'unpacked'
$elsewhere = New-Item -ItemType Directory -Force (Join-Path $work 'elsewhere')
$failures = New-Object System.Collections.Generic.List[string]
function Check([bool]$ok, [string]$what) {
    if ($ok) { Write-Host "  ok    $what" -ForegroundColor Green } else { Write-Host "  FAIL  $what" -ForegroundColor Red; $failures.Add($what) }
}

Write-Host "== Unpacking $Zip"
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::ExtractToDirectory($Zip, $unpacked)
$pkg = Join-Path $unpacked 'DelayLamaEverything'
foreach ($f in 'midis2jam2.exe', 'runtime\bin\java.exe', 'DelayLamaVoice.exe', 'DelayLamaStandalone.exe',
        'Resources\faces.png', 'Resources\background.png', 'Resources\about.png', 'Resources\DelayLama-Original-Manual.pdf',
        'profiles\imitation.json', 'NOTICE.txt', 'README.txt', 'licenses\midis2jam2-GPL-3.0.txt',
        'licenses\delalalalay-lama-MIT.txt', 'licenses\MonkSynth-MIT.txt', 'source\midis2jam2-delay-lama.patch') {
    Check (Test-Path (Join-Path $pkg $f)) "has $f"
}
# The bundle (DelayLamaBundle), when the package ships one.
$soundfonts = @(Get-ChildItem (Join-Path $pkg 'soundfonts') -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in '.sf2', '.dls' })
$cubeMaps = @(Get-ChildItem (Join-Path $pkg 'backgrounds') -Directory -ErrorAction SilentlyContinue | Where-Object {
        $names = @(Get-ChildItem $_.FullName -File | ForEach-Object { $_.BaseName.ToLower() })
        @('north', 'east', 'south', 'west', 'up', 'down' | Where-Object { $_ -notin $names }).Count -eq 0
    })
$songs = @(Get-ChildItem (Join-Path $pkg 'midi') -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in '.mid', '.midi', '.kar' })
$hasBundle = ($soundfonts.Count + $cubeMaps.Count + $songs.Count) -gt 0
if ($hasBundle) {
    Write-Host ('  bundle: {0} soundfont(s), {1} cube map(s), {2} song(s)' -f $soundfonts.Count, $cubeMaps.Count, $songs.Count)
    $notice = [IO.File]::ReadAllText((Join-Path $pkg 'NOTICE.txt'))
    Check ($notice -match 'Bundled extras') 'NOTICE.txt says whose the bundled files are'
} else {
    Write-Host '  no bundle (soundfonts\, backgrounds\, midi\)'
}

Write-Host '== Starting the launcher (from a folder outside the package)'
$err = Join-Path $work 'launcher.err.log'
$out = Join-Path $work 'launcher.out.log'
$launcher = Start-Process -FilePath (Join-Path $pkg 'midis2jam2.exe') -WorkingDirectory $elsewhere -PassThru `
    -RedirectStandardError $err -RedirectStandardOutput $out
$line = $null
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while (-not $line -and (Get-Date) -lt $deadline -and -not $launcher.HasExited) {
    Start-Sleep -Milliseconds 500
    if (Test-Path $err) {
        $line = Get-Content $err -ErrorAction SilentlyContinue | Where-Object { $_ -match 'Delay Lama: app folder' } |
            Select-Object -First 1
    }
}
$exitedEarly = $launcher.HasExited
if (-not $launcher.HasExited) {
    # The launcher's own child processes (none expected) go with it.
    & taskkill.exe /PID $launcher.Id /T /F | Out-Null
}
Check (-not $exitedEarly) 'the launcher keeps running'
Check ([bool]$line) 'the launcher logs its Delay Lama paths'
if ($line) {
    Write-Host "  $line"
    $text = $line.Substring($line.IndexOf('Delay Lama: app folder'))
    $m = [regex]::Match($text, '^Delay Lama: app folder (?<app>.*?); helper (?<helper>.*?), standalone (?<standalone>.*?), profiles (?<profiles>.*)$')
    Check $m.Success 'the log line parses'
    if ($m.Success) {
        $full = (Resolve-Path $pkg).Path.TrimEnd('\')
        Check ($m.Groups['app'].Value -ieq $full) "app folder is the package ($($m.Groups['app'].Value))"
        Check ($m.Groups['helper'].Value -ieq (Join-Path $full 'DelayLamaVoice.exe')) 'helper is the packaged DelayLamaVoice.exe'
        Check ($m.Groups['standalone'].Value -ieq (Join-Path $full 'DelayLamaStandalone.exe')) 'standalone is the packaged DelayLamaStandalone.exe'
        Check ($m.Groups['profiles'].Value -ieq (Join-Path $full 'profiles\imitation.json')) 'profiles are the packaged imitation.json'
    }
}
if ($hasBundle) {
    $bundleLine = Get-Content $err -ErrorAction SilentlyContinue | Where-Object { $_ -match 'Delay Lama: package bundle in' } |
        Select-Object -First 1
    Check ([bool]$bundleLine) 'the launcher reads the bundle'
    if ($bundleLine) {
        Write-Host "  $bundleLine"
        $full = (Resolve-Path $pkg).Path.TrimEnd('')
        Check ($bundleLine.Contains("package bundle in $full")) 'the bundle is the package''s own'
        foreach ($sf in $soundfonts) { Check ($bundleLine.Contains($sf.Name)) "the launcher found soundfont $($sf.Name)" }
        foreach ($cm in $cubeMaps) { Check ($bundleLine -match "cube maps \[([^\]]*, )?$([regex]::Escape($cm.Name))(,|\])") "the launcher found cube map $($cm.Name)" }
    }
}
$errors = @(Get-Content $err -ErrorAction SilentlyContinue | Where-Object { $_ -match ' ERROR ' })
Check ($errors.Count -eq 0) "no ERROR lines in the launcher's log ($($errors.Count))"
$errors | Select-Object -First 5 | ForEach-Object { Write-Host "    $_" }

Write-Host "== Rendering $(Split-Path $Script -Leaf) with the packaged helper"
$wav = Join-Path $work 'render.wav'
Push-Location $elsewhere
$ErrorActionPreference = 'Continue' # Windows PowerShell turns the helper's stderr summary into errors
try {
    $renderOut = & (Join-Path $pkg 'DelayLamaVoice.exe') --render $Script $wav 2>&1 | ForEach-Object { "$_" }
    $code = $LASTEXITCODE
} finally { Pop-Location; $ErrorActionPreference = 'Stop' }
Check ($code -eq 0) "DelayLamaVoice.exe --render exits 0 ($code)"
$renderOut | Select-Object -First 5 | ForEach-Object { Write-Host "    $_" }
if (Test-Path $wav) {
    $bytes = [IO.File]::ReadAllBytes($wav)
    $riff = [Text.Encoding]::ASCII.GetString($bytes, 0, 4) + [Text.Encoding]::ASCII.GetString($bytes, 8, 4)
    Check ($riff -eq 'RIFFWAVE') 'the render is a WAV file'
    # Peak of the 16-bit samples after the 44-byte header (every 8th, for speed): silence would mean the synth didn't run.
    $peak = 0
    for ($i = 44; $i + 1 -lt $bytes.Length; $i += 16) {
        $s = [Math]::Abs([int][BitConverter]::ToInt16($bytes, $i))
        if ($s -gt $peak) { $peak = $s }
    }
    Check ($peak -gt 100) ('the render is not silent ({0:N0} bytes, peak {1})' -f $bytes.Length, $peak)
} else { Check $false 'the render wrote a WAV file' }

if ($failures.Count -eq 0) {
    Write-Host "Package check passed: $Zip" -ForegroundColor Green
    if ($Keep) { Write-Host "Unpacked copy kept in $work" } else { Remove-Item -LiteralPath $work -Recurse -Force }
    exit 0
}
Write-Host "Package check FAILED ($($failures.Count)); logs and the unpacked copy are in $work" -ForegroundColor Red
exit 1
