#!/usr/bin/env python3
"""Read-only identity and optional CRC audit for the original 2012 ZOMBIEEE RAR.

The identity check is NOT an integrity test of every RAR member. A successful
7-Zip member-test (command t) can verify CRC without extracting any files.
This module never copies or modifies game assets, and its JSON omits user paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ORIGINAL_SHA256 = "9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e"
ORIGINAL_SIZE = 167493071
RAR4_MAGIC = bytes.fromhex("526172211a0700")
DEFAULT_TIMEOUT_SECONDS = 900


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_7zip() -> str | None:
    for name in ("7zz", "7z", "7za", "7z.exe", "7zz.exe"):
        exe = shutil.which(name)
        if exe:
            return exe
    for exe in (Path(r"C:\Program Files\7-Zip\7z.exe"),
                Path(r"C:\Program Files (x86)\7-Zip\7z.exe")):
        if exe.is_file():
            return str(exe)
    return None


def inspect_original_archive(path: Path, *, verify_crc: bool = False,
                             seven_zip: str | None = None,
                             expected_sha256: str = ORIGINAL_SHA256,
                             expected_size: int = ORIGINAL_SIZE,
                             timeout: int = DEFAULT_TIMEOUT_SECONDS) -> dict:
    """Return evidence statuses, never a full path or raw 7-Zip stdout.

    The overrideable expected digest and size support small deterministic tests;
    the CLI and installer must use the pinned historical values.
    """
    result = {
        "format": "RAR4", "expected_sha256": expected_sha256,
        "expected_size": expected_size, "actual_size": None,
        "actual_sha256": None, "signature_ok": False,
        "identity_ok": False, "crc_status": "not_checked",
        "seven_zip_available": False, "runtime_verified": False,
        "problems": [],
    }
    path = Path(path).expanduser()
    if not path.is_file():
        result["problems"].append("source_not_regular_file")
        return result
    try:
        result["actual_size"] = path.stat().st_size
        with path.open("rb") as stream:
            result["signature_ok"] = stream.read(len(RAR4_MAGIC)) == RAR4_MAGIC
        result["actual_sha256"] = sha256_file(path)
    except OSError:
        result["problems"].append("source_unreadable")
        return result
    if not result["signature_ok"]:
        result["problems"].append("not_rar4")
    if result["actual_size"] != expected_size:
        result["problems"].append("size_mismatch")
    if result["actual_sha256"] != expected_sha256:
        result["problems"].append("sha256_mismatch")
    result["identity_ok"] = not result["problems"]
    if not verify_crc:
        return result
    if not result["identity_ok"]:
        result["crc_status"] = "blocked_identity"
        return result
    exe = seven_zip or find_7zip()
    if not exe:
        result["crc_status"] = "unavailable"
        result["problems"].append("seven_zip_unavailable")
        return result
    result["seven_zip_available"] = True
    try:
        finished = subprocess.run(
            [str(exe), "t", "-bd", str(path.resolve())],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        result["crc_status"] = "timeout"
        result["problems"].append("seven_zip_timeout")
    except (OSError, ValueError):
        result["crc_status"] = "unavailable"
        result["problems"].append("seven_zip_failed_to_start")
    else:
        if finished.returncode == 0:
            result["crc_status"] = "verified"
        else:
            result["crc_status"] = "failed"
            result["problems"].append("seven_zip_member_test_failed")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True,
                        help="Local historical Beta 0.4 RAR; never uploaded")
    parser.add_argument("--verify-crc", action="store_true",
                        help="Run 7-Zip member CRC test without extracting")
    parser.add_argument("--seven-zip", help="Optional explicit 7-Zip path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = inspect_original_archive(args.archive, verify_crc=args.verify_crc,
                                      seven_zip=args.seven_zip)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Original archive identity:", "PASS" if report["identity_ok"] else "FAIL")
        print("RAR member CRC:", report["crc_status"])
        print("Problems:", ", ".join(report["problems"]) or "none")
        print("WSE2 gameplay: not verified")
    return 0 if report["identity_ok"] and (not args.verify_crc or report["crc_status"] == "verified") else 2


if __name__ == "__main__":
    raise SystemExit(main())
