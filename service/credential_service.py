from __future__ import annotations

import base64
import subprocess
import sys
import uuid
from ctypes import POINTER, Structure, byref, c_byte, create_string_buffer, string_at

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", POINTER(c_byte))]


def _blob(data: bytes) -> DATA_BLOB:
    import ctypes

    buffer = create_string_buffer(data)
    return DATA_BLOB(len(data), ctypes.cast(buffer, POINTER(c_byte)))


def _dpapi_encrypt(secret: str) -> str | None:
    if sys.platform != "win32":
        return None
    try:
        crypt32 = ctypes.windll.crypt32
        blob_in = _blob(secret.encode("utf-8"))
        blob_out = DATA_BLOB()
        if not crypt32.CryptProtectData(
            byref(blob_in),
            "DesktopToDo",
            None,
            None,
            None,
            0,
            byref(blob_out),
        ):
            return None
        raw = string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return "dpapi:" + base64.b64encode(raw).decode("ascii")
    except OSError:
        return None


def _keychain_service(token_id: str) -> str:
    return f"com.504615302.DesktopToDo.token.{token_id}"


def _keychain_encrypt(secret: str) -> str | None:
    if sys.platform != "darwin":
        return None
    token_id = uuid.uuid4().hex
    try:
        result = subprocess.run(
            [
                "security",
                "add-generic-password",
                "-a",
                "DesktopToDo",
                "-s",
                _keychain_service(token_id),
                "-w",
                secret,
                "-U",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return "keychain:" + token_id
    except OSError:
        pass
    return None


def _keychain_decrypt(token_id: str) -> str | None:
    if sys.platform != "darwin":
        return None
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", _keychain_service(token_id), "-w"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.rstrip("\r\n")
    except OSError:
        pass
    return None


class CredentialService:
    def encrypt(self, secret: str) -> str:
        if not secret:
            return ""
        encrypted = _dpapi_encrypt(secret) or _keychain_encrypt(secret)
        if encrypted is not None:
            return encrypted
        return base64.b64encode(secret.encode("utf-8")).decode("ascii")

    def decrypt(self, payload: str) -> str:
        if not payload:
            return ""
        try:
            if payload.startswith("dpapi:"):
                import ctypes

                raw = base64.b64decode(payload[6:])
                crypt32 = ctypes.windll.crypt32
                blob_in = _blob(raw)
                blob_out = DATA_BLOB()
                if not crypt32.CryptUnprotectData(
                    byref(blob_in), None, None, None, None, 0, byref(blob_out)
                ):
                    return ""
                text = string_at(blob_out.pbData, blob_out.cbData)
                ctypes.windll.kernel32.LocalFree(blob_out.pbData)
                return text.decode("utf-8")
            if payload.startswith("keychain:"):
                return _keychain_decrypt(payload[len("keychain:") :]) or ""
            return base64.b64decode(payload.encode("ascii")).decode("utf-8")
        except Exception:
            return ""
