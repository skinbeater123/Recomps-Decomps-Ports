param([int]$Jobs = 2, [string]$DevkitPro = 'C:\Programming\devkitPro',
    [ValidateSet('-O0','-O1','-O2')][string]$Optimization = '-O1')
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
$env:DEVKITPRO = $DevkitPro.Replace('\', '/')
$env:DEVKITA64 = "$env:DEVKITPRO/devkitA64"
python "$PSScriptRoot/generate.py" --prepare-only
if ($LASTEXITCODE -ne 0) { throw 'Runtime/executable verification failed' }
python "$PSScriptRoot/prepare_runtime.py"
if ($LASTEXITCODE -ne 0) { throw 'Runtime overlay failed' }
$env:SC1_JOBS = "$Jobs"
$env:SC1_GEN_OPT = $Optimization
& "$DevkitPro/msys2/usr/bin/bash.exe" "$PSScriptRoot/build.sh"
if ($LASTEXITCODE -ne 0) { throw 'SC1 compilation/link failed' }
Get-FileHash -LiteralPath "$project/build/switch/sc1.nro" -Algorithm SHA256
