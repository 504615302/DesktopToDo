$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    py -3 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\scripts\make_icon.py
python -m PyInstaller --noconfirm .\DesktopTODO.spec

Write-Host ""
Write-Host "Build complete: dist\DesktopTODO.exe"
