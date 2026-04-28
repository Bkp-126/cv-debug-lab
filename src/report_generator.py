"""Placeholder helpers for future Markdown report generation."""

from pathlib import Path


def build_markdown_report(title: str, output_path: str | Path) -> dict[str, str]:
    """Return placeholder metadata for a future Markdown report."""
    return {
        "title": title,
        "output_path": str(Path(output_path)),
        "status": "not_generated",
    }
