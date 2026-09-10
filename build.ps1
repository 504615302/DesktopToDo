$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    py -3 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\scripts\make_icon.py
python -m PyInstaller --noconfirm .\DesktopTODO.spec

$version = python -c "from version import __version__; print(__version__)"
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) {
    $iscc = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
}
if (Test-Path $iscc) {
    & $iscc "/DMyAppVersion=$version" .\installer\DesktopToDo.iss
    Write-Host "Installer: dist\DesktopToDo-Setup.exe"
} else {
    Write-Host "Inno Setup not found; skipped installer. Install it to also build DesktopToDo-Setup.exe."
}

Write-Host ""
Write-Host "Portable EXE: dist\DesktopTODO.exe"
