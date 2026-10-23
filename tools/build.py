#!/usr/bin/env python3
"""Prepare a clean ZOMBIEEE remaster install from a verified historical RAR.

Requires 7-Zip; does not modify or redistribute the original mod archive.
This is an installation scaffold, not proof that gameplay works on WSE2.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from doctor import inspect_module
from preflight import report_for_module
from patch_defenders import patch_file

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_SHA256 = "9be100ff41ce6f8ebadd4aa27377f70f402883fab271999a8cab8cc1da001d1e"
MODULE_NAME = "ZOMBIEEE_Remaster"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_7zip() -> str:
    for name in ("7zz", "7z", "7za", "7z.exe", "7zz.exe"):
        found = shutil.which(name)
        if found:
            return found
    for path in (
        Path(r"C:\Program Files\7-Zip\7z.exe"),
        Path(r"C:\Program Files (x86)\7-Zip\7z.exe"),
    ):
        if path.is_file():
            return str(path)
    raise RuntimeError("7-Zip not found: install 7-Zip and put 7z on PATH")


def run7(exe: str, command: str, archive: Path, output: Path | None = None) -> None:
    cmd = [exe, command, "-y", str(archive)]
    if output is not None:
        cmd.append(f"-o{output}")
    print("Running:", exe, command, "<source RAR>", flush=True)
    subprocess.run(cmd, check=True)


def rename_module_title(module_ini: Path) -> None:
    text = module_ini.read_text(encoding="utf-8", errors="replace")
    rows = text.splitlines(keepends=True)
    matched = [i for i, row in enumerate(rows) if row.strip().startswith("module_name") and "=" in row]
    if len(matched) != 1:
        raise ValueError("Expected exactly one module_name = entry in module.ini")
    ending = "\r\n" if rows[matched[0]].endswith("\r\n") else "\n"
    rows[matched[0]] = "module_name = ZOMBIEEE Remaster" + ending
    module_ini.write_text("".join(rows), encoding="utf-8")


def apply_overlay(module_dir: Path) -> None:
    for path in (ROOT / "overlay").rglob("*"):
        if path.is_file():
            destination = module_dir / path.relative_to(ROOT / "overlay")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    rename_module_title(module_dir / "module.ini")


def build(archive: Path, out: Path, replace: bool = False, experimental_defenders: int = 0) -> dict:
    if not 0 <= experimental_defenders <= 8:
        raise ValueError("--experimental-defenders must be between 0 and 8")
    archive = archive.expanduser().resolve(strict=True)
    out = out.expanduser().resolve()
    if out.name != MODULE_NAME:
        raise ValueError(f"Output directory must be named {MODULE_NAME}: {out}")
    if out.exists() and not replace:
        raise FileExistsError(f"Destination already exists (use --replace after backup): {out}")
    digest = sha256(archive)
    if digest != ORIGINAL_SHA256:
        raise ValueError("Unknown/modified archive: SHA-256 mismatch " + digest)

    exe = find_7zip()
    run7(exe, "t", archive)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="zombieee-extract-") as td:
        stage = Path(td)
        run7(exe, "x", archive, stage)
        source = stage / "ZOMBIEEE"
        if not source.is_dir():
            raise RuntimeError("Original root folder ZOMBIEEE missing after extraction")
        if not inspect_module(source)["core_ok"]:
            raise RuntimeError("Core original files/mission/five map files failed validation")
        preflight = report_for_module(source)
        if not preflight["ok"]:
            raise RuntimeError("Mission/resource preflight failed: " +
                               str(preflight.get("problems", preflight.get("error"))))
        apply_overlay(source)
        defender_report = None
        if experimental_defenders:
            defender_report = patch_file(source, experimental_defenders)
            updated = report_for_module(source)
            if not updated["ok"] or updated["mission"]["triggers"] != 26:
                raise RuntimeError("Experimental defender patch failed post-apply diagnostics")
        if not inspect_module(source)["core_ok"] or not (source / "lua" / "main.lua").is_file():
            raise RuntimeError("Module overlay failed static validation")
        (source / "ZOMBIEEE_REMASTER.json").write_text(json.dumps({
            "remaster_version": (ROOT / "VERSION").read_text().strip(),
            "source_archive_sha256": digest,
            "target": "Warband 1.174 core / WSE2 1.1.5.4",
            "runtime_verified": False,
            "preflight": preflight,
            "experimental_defender_patch": defender_report,
        }, indent=2) + "\n", encoding="utf-8")

        # Stage the final copy on the destination volume and replace atomically.
        with tempfile.TemporaryDirectory(prefix="zombieee-install-", dir=out.parent) as temp:
            candidate = Path(temp) / MODULE_NAME
            shutil.copytree(source, candidate)
            previous = None
            if out.exists():
                previous = out.with_name(out.name + ".previous")
                if previous.exists():
                    raise FileExistsError(f"Existing rollback directory must be handled first: {previous}")
                out.rename(previous)
            try:
                candidate.rename(out)
            except BaseException:
                if previous and previous.exists() and not out.exists():
                    previous.rename(out)
                raise
            else:
                if previous:
                    print(f"Previous module retained at {previous}")
    return {"module": str(out), "source_sha256": digest, "static_validation": "PASS", "experimental_defenders": experimental_defenders, "runtime_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--experimental-defenders", type=int, default=0, metavar="N", help="Opt-in 1–8 allied bots; default 0 preserves original mission")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.archive, args.out, args.replace, args.experimental_defenders), indent=2))
    except (RuntimeError, FileNotFoundError, FileExistsError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Build refused: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
