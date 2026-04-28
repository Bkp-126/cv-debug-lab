"""Placeholder helpers for future YOLO dataset auditing."""

from pathlib import Path


def summarize_yolo_dataset(dataset_dir: str | Path) -> dict[str, str]:
    """Return a minimal placeholder summary for a YOLO-style dataset."""
    return {
        "dataset_dir": str(Path(dataset_dir)),
        "status": "not_implemented",
    }
