param(
    [string]$Dotnet = 'dotnet',
    [string]$Python = 'python',
    [string]$Destination = (Join-Path $PSScriptRoot 'release\EasyResearchDesktop'),
    [string]$RuntimeArchive = ''
)
$ErrorActionPreference = 'Stop'
$Destination = [IO.Path]::GetFullPath($Destination)
# Always start from an empty folder. 'pip install --target' does not replace
# packages that are already there, so a second local build kept the old
# dependencies (and old program files) from the first one. A build on GitHub
# starts from a clean checkout and was not affected.
if (Test-Path -LiteralPath $Destination) {
    $existing = @(Get-ChildItem -LiteralPath $Destination -Force)
    if ($existing.Count -gt 0 -and -not (Test-Path -LiteralPath (Join-Path $Destination 'EasyResearchDesktop.exe'))) {
        throw "$Destination is not empty and is not an earlier EasyResearch Desktop build. Choose an empty folder with -Destination."
    }
    Write-Host "Removing the earlier build in $Destination"
    Remove-Item -LiteralPath $Destination -Recurse -Force
}
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
& $Dotnet publish (Join-Path $PSScriptRoot 'src\EasyResearch.Desktop\EasyResearch.Desktop.csproj') -c Release -r win-x64 --self-contained true --disable-build-servers -o $Destination
if ($LASTEXITCODE -ne 0) { throw 'Desktop publishing failed.' }
$runtimeFolder = Join-Path $Destination 'runtime\python'
New-Item -ItemType Directory -Path $runtimeFolder -Force | Out-Null
if (-not $RuntimeArchive) {
    $RuntimeArchive = Join-Path $PSScriptRoot 'release\python-3.12.8-embed-amd64.zip'
    Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip' -OutFile $RuntimeArchive
}
Expand-Archive -LiteralPath $RuntimeArchive -DestinationPath $runtimeFolder -Force
@('python312.zip', '.', 'Lib/site-packages', 'import site') | Set-Content -LiteralPath (Join-Path $runtimeFolder 'python312._pth') -Encoding ascii
& $Python -m pip install --only-binary=:all: --target (Join-Path $runtimeFolder 'Lib\site-packages') -r (Join-Path $PSScriptRoot 'requirements.lock.txt')
if ($LASTEXITCODE -ne 0) { throw 'Bundled analysis dependencies could not be installed.' }
# PyTorch (forecasting and signal classification) needs the Microsoft Visual
# C++ runtime: msvcp140.dll and, in recent builds, vcruntime140_threads.dll.
# The embedded Python ships only vcruntime140.dll and vcruntime140_1.dll, and a
# clean Windows computer has no runtime installed, so both tasks failed to load.
# The runtime files are copied next to python.exe (app-local deployment, which
# the Visual Studio redistribution terms allow), all from one runtime version.
$crtFiles = @('msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll', 'msvcp140_atomic_wait.dll',
              'msvcp140_codecvt_ids.dll', 'vcruntime140.dll', 'vcruntime140_1.dll',
              'vcruntime140_threads.dll', 'concrt140.dll')
$crtFolder = $null
$vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
if (Test-Path -LiteralPath $vswhere) {
    $vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if ($vs) {
        $crtFolder = Get-ChildItem -Path (Join-Path $vs 'VC\Redist\MSVC\*\x64\Microsoft.VC14*.CRT') -Directory -ErrorAction SilentlyContinue |
            Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'vcruntime140_threads.dll') } |
            Sort-Object { try { [version]$_.Parent.Parent.Name } catch { [version]'0.0' } } |
            Select-Object -Last 1 -ExpandProperty FullName
    }
}
if (-not $crtFolder) { $crtFolder = Join-Path $env:SystemRoot 'System32' }
foreach ($name in $crtFiles) {
    $source = Join-Path $crtFolder $name
    if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination $runtimeFolder -Force }
}
foreach ($name in @('msvcp140.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'vcruntime140_threads.dll')) {
    if (-not (Test-Path -LiteralPath (Join-Path $runtimeFolder $name))) {
        throw "The Visual C++ runtime file $name was not found in $crtFolder. Install the latest Visual C++ Redistributable (x64) on the build computer: https://aka.ms/vs/17/release/vc_redist.x64.exe"
    }
}
Write-Host "Visual C++ runtime bundled from $crtFolder"
# The analysis cores come from the EasyResearch source next to this folder,
# so the desktop runs exactly the code the command line runs. Their
# dependencies, including statsmodels and the CPU build of PyTorch used by
# forecasting, are pinned in requirements.lock.txt.
$wheelFolder = Join-Path $PSScriptRoot 'release\wheels'
# Wheels left from an earlier build must not be picked up instead of the new one.
if (Test-Path -LiteralPath $wheelFolder) { Remove-Item -LiteralPath $wheelFolder -Recurse -Force }
New-Item -ItemType Directory -Path $wheelFolder -Force | Out-Null
# EasyClassifier comes from PyPI at the version pinned in the lock file; EasyResearch is bundled from
# the source in this repository, so the portable application always matches the code that was tested.
foreach ($package in @(@{ Name = 'easyresearch'; Source = '..' })) {
    & $Python -m pip wheel --no-deps -w $wheelFolder (Join-Path $PSScriptRoot $package.Source)
    if ($LASTEXITCODE -ne 0) { throw "The $($package.Name) package could not be built." }
    $wheel = Get-ChildItem -LiteralPath $wheelFolder -Filter "$($package.Name)-*.whl" | Sort-Object LastWriteTime | Select-Object -Last 1
    & $Python -m pip install --no-deps --upgrade --force-reinstall --target (Join-Path $runtimeFolder 'Lib\site-packages') $wheel.FullName
    if ($LASTEXITCODE -ne 0) { throw "The $($package.Name) package could not be bundled." }
}
# Every bundled package must be exactly the version in requirements.lock.txt,
# installed once (two .dist-info folders mean an old copy was left behind).
$sitePackages = Join-Path $runtimeFolder 'Lib\site-packages'
$installed = @(Get-ChildItem -LiteralPath $sitePackages -Directory -Filter '*.dist-info')
$problems = @()
foreach ($line in Get-Content -LiteralPath (Join-Path $PSScriptRoot 'requirements.lock.txt')) {
    if ($line -notmatch '^\s*([A-Za-z0-9_.\-]+)==([^\s;#]+)') { continue }
    $name = ($Matches[1] -replace '[-_.]+', '_').ToLowerInvariant()
    $wanted = $Matches[2]
    $found = @($installed | Where-Object { ($_.Name -replace '\.dist-info$', '') -match '^(.+)-([^-]+)$' -and
                                           (($Matches[1] -replace '[-_.]+', '_').ToLowerInvariant() -eq $name) })
    if ($found.Count -ne 1) { $problems += "$name`: $($found.Count) installed copies" }
    elseif ($found[0].Name -notmatch ('-' + [regex]::Escape($wanted) + '\.dist-info$')) { $problems += "$name`: $($found[0].Name), expected $wanted" }
}
$own = @($installed | Where-Object { $_.Name -like 'easyresearch-*' })
if ($own.Count -ne 1) { $problems += "easyresearch: $($own.Count) installed copies" }
if ($problems) { throw "The bundled Python packages do not match requirements.lock.txt:`n" + ($problems -join "`n") }
Write-Host "Bundled packages match requirements.lock.txt ($($installed.Count) packages)."
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'PORTABLE-README.txt') -Destination $Destination -Force
Write-Host "Portable application: $Destination\EasyResearchDesktop.exe"
