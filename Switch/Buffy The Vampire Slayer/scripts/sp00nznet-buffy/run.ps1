# Bounded private boot of the Buffy sp00nznet build. Writes logs and flip BMPs under runs\<stamp>.
param([int]$Seconds = 120, [string]$Label = "boot", [switch]$Window, [int]$SampleSecs = 0, [int]$WatchdogSecs = 20, [switch]$KeepSave, [switch]$TraceArgs, [switch]$ReportDumpsOnly)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$exe = Join-Path $root 'build\buffy_recomp.exe'
$run = Join-Path $root ("runs\{0}-{1}" -f (Get-Date -Format 'yyyyMMdd-HHmmss'), $Label)
New-Item -ItemType Directory -Force (Join-Path $run 'frames') | Out-Null

$env:RECOMP_PB_EXEC = '1'                                   # execute the NV2A pushbuffer (CPU rasteriser)
$env:RECOMP_FB_DUMP = (Join-Path $run 'frames\fb_')         # BMP prefix
if ($ReportDumpsOnly) { Remove-Item Env:RECOMP_FB_DUMP_FLIPS -ErrorAction SilentlyContinue }
else { $env:RECOMP_FB_DUMP_FLIPS = '1' }                    # one BMP per presented flip
$env:RECOMP_AC97_READY = '1'                                # emulated APU so DirectSoundCreate can pass
$env:RECOMP_WATCHDOG_SECS = "$WatchdogSecs"                    # report where the guest sits if it hangs
if ($SampleSecs -gt 0) { $env:RECOMP_SAMPLE_SECS = "$SampleSecs" } else { Remove-Item Env:RECOMP_SAMPLE_SECS -ErrorAction SilentlyContinue }
$env:RECOMP_MISSING_FILES = '1'                             # log files the title asks for and lacks
if (-not $Window) { $env:RECOMP_HEADLESS = '1' }
if ($TraceArgs) { $env:RECOMP_TRACE_ARGS = '1' } else { Remove-Item Env:RECOMP_TRACE_ARGS -ErrorAction SilentlyContinue }

# First-boot conditions: an empty HDD (no TDATA/UDATA, no Z: cache, no partition images).
if (-not $KeepSave) { Remove-Item -Recurse -Force (Join-Path $root 'save') -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Force (Join-Path $root 'save') | Out-Null

# The exe resolves game\ and save\ relative to its working directory.
$p = Start-Process -FilePath $exe -WorkingDirectory $root -PassThru -NoNewWindow `
    -RedirectStandardOutput (Join-Path $run 'stdout.txt') -RedirectStandardError (Join-Path $run 'stderr.txt')
$exited = $p.WaitForExit($Seconds * 1000)
if (-not $exited) { Stop-Process -Id $p.Id -Force; $p.WaitForExit() }
$frames = @(Get-ChildItem (Join-Path $run 'frames') -Filter *.bmp -ErrorAction SilentlyContinue)
[pscustomobject]@{
    run = $run; exited_by_itself = $exited; exit_code = $(if ($exited) { $p.ExitCode } else { 'killed' })
    seconds = $Seconds; flip_bmps = $frames.Count
    stderr_lines = (Get-Content (Join-Path $run 'stderr.txt') -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
} | ConvertTo-Json | Tee-Object (Join-Path $run 'summary.json')
