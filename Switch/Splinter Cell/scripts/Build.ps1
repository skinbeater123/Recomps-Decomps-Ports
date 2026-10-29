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

$buildId = (Get-Content -LiteralPath "$project/build/switch/build-id.txt" -Raw).Trim()
if ($buildId -notmatch '^[A-Za-z0-9.-]+$') { throw 'Invalid SC1 build identity' }
foreach ($ext in @('nro','elf')) {
    Copy-Item -LiteralPath "$project/build/switch/sc1.$ext" -Destination "$project/build/switch/sc1-$buildId.$ext"
}
$artifact = Join-Path $project "private/artifacts/sc1-$buildId"
New-Item -ItemType Directory -Path $artifact -Force | Out-Null
$hashes = [ordered]@{}
foreach ($ext in @('nro','elf')) {
    $source = "$project/build/switch/sc1.$ext"
    Copy-Item -LiteralPath $source -Destination "$artifact/sc1-$buildId.$ext"
    $hashes[$ext] = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
}
$generatedHashes = [ordered]@{}
Get-ChildItem -LiteralPath "$project/generated" -File | Sort-Object Name | ForEach-Object {
    $generatedHashes[$_.Name] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
[ordered]@{ build_id = $buildId; optimization = $Optimization; artifacts = $hashes;
    generated_source_sha256 = $generatedHashes; console_tested = $false } |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$artifact/checksums.json" -Encoding utf8
Write-Output "SC1 build: $buildId"
