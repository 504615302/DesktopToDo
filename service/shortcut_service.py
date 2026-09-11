from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from app_paths import exe_dir, icon_path, is_frozen
from version import APP_DISPLAY_NAME

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def persistent_icon_path() -> Path | None:
    source = icon_path("app.ico")
    if not source.exists():
        return None
    if not is_frozen():
        return source
    dest = exe_dir() / "app.ico"
    if dest.resolve() != source.resolve():
        try:
            dest.write_bytes(source.read_bytes())
        except OSError:
            return source
    return dest if dest.exists() else source


def desktop_dir() -> Path:
    return Path.home() / "Desktop"


def desktop_shortcut_path() -> Path:
    return desktop_dir() / f"{APP_DISPLAY_NAME}.lnk"


def sync_desktop_shortcut_icon() -> None:
    icon = persistent_icon_path()
    lnk = desktop_shortcut_path()
    if icon is None or not lnk.exists():
        return
    _update_shortcut_icon(lnk, icon)


def _ps_quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _update_shortcut_icon(lnk: Path, icon: Path) -> None:
    script = (
        "$ErrorActionPreference = 'Stop'\n"
        "$sh = New-Object -ComObject WScript.Shell\n"
        f"$s = $sh.CreateShortcut({_ps_quote(str(lnk))})\n"
        "$target = $s.TargetPath\n"
        f"$icon = {_ps_quote(str(icon))}\n"
        "if ($target) {\n"
        "  $sidecar = Join-Path ([System.IO.Path]::GetDirectoryName($target)) 'app.ico'\n"
        "  try {\n"
        "    Copy-Item -LiteralPath $icon -Destination $sidecar -Force\n"
        "    $icon = $sidecar\n"
        "  } catch {}\n"
        "}\n"
        "$s.IconLocation = ($icon + ',0')\n"
        "$s.Save()\n"
    )
    path = ""
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8-sig") as handle:
            handle.write(script)
            path = handle.name
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path],
            check=False,
            creationflags=CREATE_NO_WINDOW,
        )
    except OSError:
        return
    finally:
        if path:
            Path(path).unlink(missing_ok=True)
