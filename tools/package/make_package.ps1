<#
.SYNOPSIS
    Builds Delay Lama Everything's Windows package into dist\ and zips it.

.DESCRIPTION
    Builds midis2jam2's jpackage app image (Compose Desktop's :app:createDistributable, from
    external\midis2jam2 as it is checked out), then adds next to its midis2jam2.exe:
    DelayLamaVoice.exe, DelayLamaStandalone.exe and their Resources\ (copied from
    external\delalalalay-lama\Windows\build\Release\, built beforehand unless -BuildDelayLama),
    profiles\imitation.json, the license notices and the source of our midis2jam2 changes, plus the bundle
    (soundfonts, cube maps and songs from bundle\ unless -NoBundle). The launcher finds the three Delay Lama files
    next to itself (catalogue entry delaylama.package.locate) and uses the bundle on its first start
    (delaylama.package.bundle). See tools\package\README.md.

.EXAMPLE
    .\tools\package\make_package.ps1
    .\tools\package\make_package.ps1 -SkipBuild -Version test
#>
[CmdletBinding()]
param(
    # Name part of the zip: DelayLamaEverything-<Version>-windows-x64.zip. Default: today's date.
    [string]$Version = (Get-Date -Format 'yyyy-MM-dd'),
    # Where the package folder and the zip go.
    [string]$OutDir,
    # JDK 21 that builds midis2jam2; its java.exe and javaw.exe go into the package's runtime.
    [string]$Jdk = 'C:\Program Files\Java\jdk-21',
    # Android SDK (midis2jam2's Gradle build needs it even for desktop tasks).
    [string]$AndroidSdk = (Join-Path $env:LOCALAPPDATA 'Android\Sdk'),
    # Reuse the app image already built in external\midis2jam2 instead of running Gradle.
    [switch]$SkipBuild,
    # Also build external\delalalalay-lama with CMake first (off by default: another session may own that build).
    [switch]$BuildDelayLama,
    # Leave the folder in dist\ but don't zip it.
    [switch]$NoZip,
    # The extras to ship: soundfonts\, backgrounds\<cube map>\, midi\, licenses\ and NOTICE.txt. Default: bundle\.
    [string]$Bundle,
    # Ship without the bundle.
    [switch]$NoBundle
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 3

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$M2j = Join-Path $Root 'external\midis2jam2'
$Dl = Join-Path $Root 'external\delalalalay-lama'
$Release = Join-Path $Dl 'Windows\build\Release'
$Image = Join-Path $M2j 'app\build\compose\binaries\main\app\midis2jam2'
if (-not $OutDir) { $OutDir = Join-Path $Root 'dist' }
if (-not $Bundle) { $Bundle = Join-Path $Root 'bundle' }
$PackageName = 'DelayLamaEverything'
$Stage = Join-Path $OutDir $PackageName
$Zip = Join-Path $OutDir "$PackageName-$Version-windows-x64.zip"

function Step([string]$text) { Write-Host "== $text" -ForegroundColor Cyan }

function Invoke-Native([string]$exe, [string[]]$arguments, [string]$where) {
    Push-Location $where
    try {
        & $exe @arguments
        if ($LASTEXITCODE -ne 0) { throw "$exe $($arguments -join ' ') failed with exit code $LASTEXITCODE" }
    } finally { Pop-Location }
}

# A running helper or a linker may hold an exe; wait and retry instead of failing at once.
function Copy-WithRetry([string]$from, [string]$to, [int]$tries = 20) {
    for ($i = 1; $i -le $tries; $i++) {
        try { Copy-Item -LiteralPath $from -Destination $to -Force; return }
        catch {
            if ($i -eq $tries) { throw }
            Write-Warning "Can't copy $from yet ($($_.Exception.Message)); retrying in 3 s"
            Start-Sleep -Seconds 3
        }
    }
}

function Invoke-Git([string]$repo, [string[]]$arguments) {
    $out = & git.exe -c core.safecrlf=false -C $repo @arguments
    if ($LASTEXITCODE -ne 0) { throw "git $($arguments -join ' ') failed in $repo" }
    return $out
}

function Write-Utf8([string]$path, [string]$text) {
    [IO.File]::WriteAllText($path, $text.Replace("`r`n", "`n").Replace("`n", "`r`n"), (New-Object Text.UTF8Encoding $false))
}

# --- 1. Build -----------------------------------------------------------------------------------

if ($BuildDelayLama) {
    Step 'Building delalalalay-lama (CMake, Release)'
    Invoke-Native 'cmake' @('-S', '.\Windows', '-B', '.\Windows\build', '-G', 'Visual Studio 17 2022', '-A', 'x64') $Dl
    Invoke-Native 'cmake' @('--build', '.\Windows\build', '--config', 'Release', '--parallel') $Dl
}
foreach ($f in 'DelayLamaVoice.exe', 'DelayLamaStandalone.exe', 'Resources\faces.png') {
    if (-not (Test-Path (Join-Path $Release $f))) { throw "$f is missing in $Release; build delalalalay-lama first (or pass -BuildDelayLama)" }
}

if (-not $SkipBuild) {
    Step 'Building the midis2jam2 app image (:app:createDistributable)'
    if (-not (Test-Path (Join-Path $Jdk 'bin\jpackage.exe'))) { throw "No JDK with jpackage at $Jdk (pass -Jdk)" }
    $env:JAVA_HOME = $Jdk
    $env:ANDROID_HOME = $AndroidSdk
    Invoke-Native (Join-Path $M2j 'gradlew.bat') @(':app:createDistributable', '--console=plain') $M2j
}
if (-not (Test-Path (Join-Path $Image 'midis2jam2.exe'))) { throw "No app image at $Image (run without -SkipBuild)" }

# --- 2. Collect ---------------------------------------------------------------------------------

Step "Collecting into $Stage"
if (Test-Path $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force }
New-Item -ItemType Directory -Force $Stage | Out-Null
Copy-Item -Path (Join-Path $Image '*') -Destination $Stage -Recurse

# Recording starts a renderer JVM from runtime\bin\java.exe, which jlink left out of the image.
$runtimeBin = Join-Path $Stage 'runtime\bin'
if (-not (Test-Path (Join-Path $runtimeBin 'java.exe'))) {
    # Only from the very JDK jlink made the runtime from: its JVM must be the same file.
    $want = (Get-FileHash (Join-Path $runtimeBin 'server\jvm.dll')).Hash
    $have = (Get-FileHash (Join-Path $Jdk 'bin\server\jvm.dll')).Hash
    if ($want -ne $have) { throw "The image's runtime wasn't made from the JDK at $Jdk; can't add its java.exe (pass -Jdk)" }
    Copy-Item (Join-Path $Jdk 'bin\java.exe'), (Join-Path $Jdk 'bin\javaw.exe') $runtimeBin
}

foreach ($exe in 'DelayLamaVoice.exe', 'DelayLamaStandalone.exe') {
    Copy-WithRetry (Join-Path $Release $exe) (Join-Path $Stage $exe)
}
# All of the AudioNerdz files travel together (their terms), the manual included.
Copy-Item -Path (Join-Path $Release 'Resources') -Destination $Stage -Recurse
New-Item -ItemType Directory -Force (Join-Path $Stage 'profiles') | Out-Null
Copy-Item (Join-Path $Root 'profiles\imitation.json') (Join-Path $Stage 'profiles\imitation.json')

$licenses = New-Item -ItemType Directory -Force (Join-Path $Stage 'licenses')
Copy-Item (Join-Path $M2j 'LICENSE') (Join-Path $licenses 'midis2jam2-GPL-3.0.txt')
Copy-Item (Join-Path $Dl 'LICENSE') (Join-Path $licenses 'delalalalay-lama-MIT.txt')
Copy-Item (Join-Path $Dl 'MONKSYNTH-LICENSE.txt') (Join-Path $licenses 'MonkSynth-MIT.txt')
$notices = Join-Path $M2j 'app\src\commonMain\composeResources\files\THIRD-PARTY-NOTICES.txt'
if (Test-Path $notices) { Copy-Item $notices (Join-Path $licenses 'midis2jam2-THIRD-PARTY-NOTICES.txt') }

# The bundle: soundfonts, cube maps and songs the app picks up on its first start (DelayLamaBundle).
$bundleNotice = ''
$bundleReadme = ''
if (-not $NoBundle) {
    Step "Adding the bundle from $Bundle"
    if (-not (Test-Path $Bundle)) { throw "No bundle folder at $Bundle (pass -Bundle, or -NoBundle)" }
    $shipped = @()
    foreach ($part in 'soundfonts', 'backgrounds', 'midi') {
        $from = Join-Path $Bundle $part
        if (-not (Test-Path $from)) { continue }
        Copy-Item -LiteralPath $from -Destination (Join-Path $Stage $part) -Recurse
        $shipped += $part
    }
    if (Test-Path (Join-Path $Bundle 'licenses')) {
        Copy-Item -Path (Join-Path $Bundle 'licenses\*') -Destination $licenses -Recurse
    }
    if (-not $shipped) { throw "The bundle at $Bundle has no soundfonts\, backgrounds\ or midi\ (pass -NoBundle to ship without)" }
    $noticeFile = Join-Path $Bundle 'NOTICE.txt'
    if (-not (Test-Path $noticeFile)) { throw "The bundle at $Bundle has no NOTICE.txt saying whose its files are" }
    $bundleNotice = "`n" + [IO.File]::ReadAllText($noticeFile).TrimEnd()
    $bundleReadme = "`n" + [IO.File]::ReadAllText((Join-Path $PSScriptRoot 'package-README-bundle.txt')).TrimEnd() + "`n"
    $sizes = foreach ($part in $shipped) {
        $mb = (Get-ChildItem -LiteralPath (Join-Path $Stage $part) -Recurse -File | Measure-Object Length -Sum).Sum / 1MB
        '{0} {1:N0} MB' -f $part, $mb
    }
    Write-Host "  $($sizes -join ', ')"
}

# --- 3. Source of our midis2jam2 changes (GPL-3.0) ------------------------------------------------

Step 'Writing the source of the midis2jam2 changes'
$source = New-Item -ItemType Directory -Force (Join-Path $Stage 'source')
$base = (Invoke-Git $M2j @('merge-base', 'HEAD', 'origin/master')) | Select-Object -First 1
$head = (Invoke-Git $M2j @('rev-parse', 'HEAD')) | Select-Object -First 1
$branch = (Invoke-Git $M2j @('rev-parse', '--abbrev-ref', 'HEAD')) | Select-Object -First 1
$dirty = [bool](Invoke-Git $M2j @('status', '--porcelain', '--untracked-files=normal'))
$patch = Join-Path $source 'midis2jam2-delay-lama.patch'
Invoke-Git $M2j @('diff', '--binary', "--output=$patch", $base, '--') | Out-Null
# Files git doesn't track yet are in the build too: append them as new files.
$untracked = @(Invoke-Git $M2j @('ls-files', '--others', '--exclude-standard', '--', 'app', 'asset-tools', 'gradle', 'build.gradle.kts', 'settings.gradle.kts', 'gradle.properties'))
foreach ($file in $untracked) {
    if (-not $file) { continue }
    $part = Join-Path $env:TEMP "dle-untracked-$([guid]::NewGuid()).patch"
    & git.exe -c core.safecrlf=false -C $M2j diff --no-index --binary "--output=$part" -- /dev/null $file
    if ($LASTEXITCODE -gt 1) { throw "git diff --no-index failed for $file" }
    [IO.File]::AppendAllText($patch, [IO.File]::ReadAllText($part))
    Remove-Item $part
}
$dlHead = (Invoke-Git $Dl @('rev-parse', 'HEAD')) | Select-Object -First 1
$dlBranch = (Invoke-Git $Dl @('rev-parse', '--abbrev-ref', 'HEAD')) | Select-Object -First 1
$dlDirty = [bool](Invoke-Git $Dl @('status', '--porcelain', '--untracked-files=no'))

$state = if ($dirty) { "commit $head plus uncommitted changes (all in the patch)" } else { "commit $head" }
$dlState = if ($dlDirty) { "commit $dlHead plus uncommitted changes in its working tree" } else { "commit $dlHead" }
$built = Get-Date -Format 'yyyy-MM-dd HH:mm'

$templates = $PSScriptRoot
$fill = @{
    '{{VERSION}}' = $Version; '{{BUILT}}' = $built
    '{{M2J_BASE}}' = $base; '{{M2J_BRANCH}}' = $branch; '{{M2J_STATE}}' = $state
    '{{DL_BRANCH}}' = $dlBranch; '{{DL_STATE}}' = $dlState
    '{{BUNDLE_NOTICE}}' = $bundleNotice; '{{BUNDLE_README}}' = $bundleReadme
}
foreach ($name in 'README.txt', 'NOTICE.txt') {
    $text = [IO.File]::ReadAllText((Join-Path $templates "package-$name"))
    foreach ($key in $fill.Keys) { $text = $text.Replace($key, $fill[$key]) }
    Write-Utf8 (Join-Path $Stage $name) $text
}

# --- 4. Zip -------------------------------------------------------------------------------------

if (-not $NoZip) {
    Step "Zipping to $Zip"
    if (Test-Path $Zip) { Remove-Item -LiteralPath $Zip -Force }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::CreateFromDirectory($Stage, $Zip, [IO.Compression.CompressionLevel]::Optimal, $true)
    $size = (Get-Item $Zip).Length / 1MB
    Write-Host ('Package: {0} ({1:N1} MB)' -f $Zip, $size) -ForegroundColor Green
} else {
    Write-Host "Package folder: $Stage" -ForegroundColor Green
}
