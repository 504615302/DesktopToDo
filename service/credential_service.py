from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes) -> DATA_BLOB:
    buffer = ctypes.create_string_buffer(data)
    return DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))


class CredentialService:
    def encrypt(self, secret: str) -> str:
        if not secret:
            return ""
        try:
            crypt32 = ctypes.windll.crypt32
            blob_in = _blob(secret.encode("utf-8"))
            blob_out = DATA_BLOB()
            if not crypt32.CryptProtectData(
                ctypes.byref(blob_in),
                "DesktopToDo",
                None,
                None,
                None,
                0,
                ctypes.byref(blob_out),
            ):
                return base64.b64encode(secret.encode("utf-8")).decode("ascii")
            raw = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            ctypes.windll.kernel32.LocalFree(blob_out.pbData)
            return "dpapi:" + base64.b64encode(raw).decode("ascii")
        except OSError:
            return base64.b64encode(secret.encode("utf-8")).decode("ascii")

    def decrypt(self, payload: str) -> str:
        if not payload:
            return ""
        try:
            if payload.startswith("dpapi:"):
                raw = base64.b64decode(payload[6:])
                crypt32 = ctypes.windll.crypt32
                blob_in = _blob(raw)
                blob_out = DATA_BLOB()
                if not crypt32.CryptUnprotectData(
                    ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
                ):
                    return ""
                text = ctypes.string_at(blob_out.pbData, blob_out.cbData)
                ctypes.windll.kernel32.LocalFree(blob_out.pbData)
                return text.decode("utf-8")
            return base64.b64decode(payload.encode("ascii")).decode("utf-8")
        except Exception:
            return ""
