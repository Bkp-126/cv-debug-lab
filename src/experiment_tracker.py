"""Placeholder helpers for future experiment tracking."""

from pathlib import Path


def initialize_experiment_store(db_path: str | Path) -> Path:
    """Return the target SQLite path for a future experiment store."""
    return Path(db_path)


def record_experiment_note(note: str) -> dict[str, str]:
    """Return a placeholder experiment note record."""
    return {
        "note": note,
        "status": "not_persisted",
    }
