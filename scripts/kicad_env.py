"""Shared helpers to locate KiCad tools and project paths."""

import os
import shutil
from pathlib import Path

PROJECT_NAME = "OOTY"
PROJECT_DIR = Path(__file__).resolve().parent.parent

_DEFAULT_KICAD_BIN = Path(r"C:\Program Files\KiCad\10.0\bin")


def kicad_cli() -> str:
    """Return the kicad-cli executable (KICAD_CLI env var, PATH, then default install)."""
    env = os.environ.get("KICAD_CLI")
    if env:
        return env
    found = shutil.which("kicad-cli")
    if found:
        return found
    default = _DEFAULT_KICAD_BIN / "kicad-cli.exe"
    if default.exists():
        return str(default)
    raise FileNotFoundError("kicad-cli not found: set KICAD_CLI or add KiCad bin to PATH")


def project_file(ext: str) -> Path:
    """Return the path of the project file with the given extension (e.g. '.kicad_sch')."""
    return PROJECT_DIR / f"{PROJECT_NAME}{ext}"
