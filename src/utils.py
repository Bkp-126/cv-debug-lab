"""Shared utility placeholders for cv-debug-lab."""

from pathlib import Path


def project_root() -> Path:
    """Return the repository root path."""
    return Path(__file__).resolve().parents[1]
