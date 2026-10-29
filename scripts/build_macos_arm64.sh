#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "This build must run on macOS with Apple Silicon (arm64)." >&2
  exit 1
fi

python3 -m venv .venv-macos
# shellcheck disable=SC1091
source .venv-macos/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

icon_dir="resources/icons"
iconset="$icon_dir/app.iconset"
rm -rf "$iconset"
mkdir -p "$iconset"

resize_icon() {
  local size="$1"
  local name="$2"
  sips -z "$size" "$size" "$icon_dir/app.png" --out "$iconset/$name" >/dev/null
}

resize_icon 16 "icon_16x16.png"
resize_icon 32 "icon_16x16@2x.png"
resize_icon 32 "icon_32x32.png"
resize_icon 64 "icon_32x32@2x.png"
resize_icon 128 "icon_128x128.png"
resize_icon 256 "icon_128x128@2x.png"
resize_icon 256 "icon_256x256.png"
resize_icon 512 "icon_256x256@2x.png"
resize_icon 512 "icon_512x512.png"
resize_icon 1024 "icon_512x512@2x.png"
iconutil -c icns "$iconset" -o "$icon_dir/app.icns"
rm -rf "$iconset"

rm -rf build/DesktopTODO dist/DesktopTODO.app
python -m PyInstaller --noconfirm --clean DesktopTODO.mac.spec

codesign --force --deep --sign - dist/DesktopTODO.app
codesign --verify --strict dist/DesktopTODO.app

version="$(python -c 'from version import __version__; print(__version__)')"
artifact="dist/DesktopToDo-macos-arm64-v${version}.tar.gz"
COPYFILE_DISABLE=1 tar --exclude .DS_Store -czf "$artifact" -C dist DesktopTODO.app
shasum -a 256 "$artifact" > "${artifact}.sha256"

echo "macOS artifact: $artifact"
