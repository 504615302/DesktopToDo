from __future__ import annotations

import base64
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from service import credential_service

CredentialService = credential_service.CredentialService


class CredentialServiceTests(unittest.TestCase):
    def test_macos_keychain_roundtrip(self) -> None:
        result = SimpleNamespace(returncode=0, stdout="sk-test\n")
        with (
            patch.object(credential_service.sys, "platform", "darwin"),
            patch.object(credential_service.subprocess, "run", return_value=result),
        ):
            service = CredentialService()
            payload = service.encrypt("sk-test")

            self.assertTrue(payload.startswith("keychain:"))
            self.assertEqual(service.decrypt(payload), "sk-test")

    def test_macos_keychain_failure_falls_back_to_portable_payload(self) -> None:
        result = SimpleNamespace(returncode=51, stdout="")
        with (
            patch.object(credential_service.sys, "platform", "darwin"),
            patch.object(credential_service.subprocess, "run", return_value=result),
        ):
            service = CredentialService()
            payload = service.encrypt("sk-test")

            self.assertEqual(payload, base64.b64encode(b"sk-test").decode("ascii"))
            self.assertEqual(service.decrypt(payload), "sk-test")

    @unittest.skipIf(sys.platform != "win32", "DPAPI is only available on Windows")
    def test_windows_dpapi_roundtrip(self) -> None:
        service = CredentialService()
        payload = service.encrypt("sk-test")

        self.assertTrue(payload.startswith("dpapi:"))
        self.assertEqual(service.decrypt(payload), "sk-test")


if __name__ == "__main__":
    unittest.main()
