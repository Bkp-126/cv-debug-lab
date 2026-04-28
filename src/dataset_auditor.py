"""YOLO dataset auditing helpers for cv-debug-lab."""

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SPLITS = ("train", "val")


def _list_images(directory: Path) -> dict[str, Path]:
    """Return image files keyed by stem."""
    if not directory.exists():
        return {}
    return {
        path.stem: path
        for path in sorted(directory.iterdir())
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    }


def _list_labels(directory: Path) -> dict[str, Path]:
    """Return YOLO label files keyed by stem."""
    if not directory.exists():
        return {}
    return {
        path.stem: path
        for path in sorted(directory.iterdir())
        if path.is_file() and path.suffix.lower() == ".txt"
    }


def _relative(path: Path, base: Path) -> str:
    """Return a readable path relative to the dataset root when possible."""
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def _issue(
    split: str,
    issue_type: str,
    path: Path,
    dataset_dir: Path,
    message: str,
    line: int | None = None,
) -> dict[str, Any]:
    """Create a normalized issue item for display and reporting."""
    item: dict[str, Any] = {
        "split": split,
        "type": issue_type,
        "path": _relative(path, dataset_dir),
        "message": message,
    }
    if line is not None:
        item["line"] = line
    return item


def _parse_label_file(
    label_path: Path,
    split: str,
    dataset_dir: Path,
) -> tuple[int, Counter[str], list[dict[str, Any]]]:
    """Parse a YOLO label file and return box count, classes, and issues."""
    class_counts: Counter[str] = Counter()
    issues: list[dict[str, Any]] = []

    try:
        raw_lines = label_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        raw_lines = label_path.read_text(encoding="utf-8", errors="replace").splitlines()

    non_empty_lines = [line for line in raw_lines if line.strip()]
    if not non_empty_lines:
        issues.append(
            _issue(
                split,
                "empty_label",
                label_path,
                dataset_dir,
                "Label file is empty.",
            )
        )
        return 0, class_counts, issues

    box_count = 0
    for line_number, line in enumerate(raw_lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        parts = stripped.split()
        if len(parts) != 5:
            issues.append(
                _issue(
                    split,
                    "invalid_label_format",
                    label_path,
                    dataset_dir,
                    "Expected 5 values: class_id x_center y_center width height.",
                    line=line_number,
                )
            )
            continue

        class_id, *bbox_values = parts
        try:
            x_center, y_center, width, height = [float(value) for value in bbox_values]
        except ValueError:
            issues.append(
                _issue(
                    split,
                    "invalid_label_format",
                    label_path,
                    dataset_dir,
                    "Bounding box values must be numeric.",
                    line=line_number,
                )
            )
            continue

        box_count += 1
        class_counts[class_id] += 1

        if width <= 0 or height <= 0:
            issues.append(
                _issue(
                    split,
                    "invalid_bbox_size",
                    label_path,
                    dataset_dir,
                    "Bounding box width and height must be greater than 0.",
                    line=line_number,
                )
            )

        values_in_range = all(
            0 <= value <= 1 for value in (x_center, y_center, width, height)
        )
        box_in_frame = (
            x_center - width / 2 >= 0
            and y_center - height / 2 >= 0
            and x_center + width / 2 <= 1
            and y_center + height / 2 <= 1
        )
        if not values_in_range or not box_in_frame:
            issues.append(
                _issue(
                    split,
                    "bbox_out_of_bounds",
                    label_path,
                    dataset_dir,
                    "Bounding box is outside the normalized image area.",
                    line=line_number,
                )
            )

    return box_count, class_counts, issues


def audit_yolo_dataset(dataset_dir: str | Path) -> dict[str, Any]:
    """Scan a YOLO dataset and return structured quality statistics."""
    dataset_path = Path(dataset_dir)
    issues: list[dict[str, Any]] = []
    class_distribution: Counter[str] = Counter()
    boxes_per_image: list[dict[str, Any]] = []
    split_stats: dict[str, dict[str, Any]] = {}

    for split in SPLITS:
        image_dir = dataset_path / "images" / split
        label_dir = dataset_path / "labels" / split
        images = _list_images(image_dir)
        labels = _list_labels(label_dir)

        missing_label_stems = sorted(set(images) - set(labels))
        orphan_label_stems = sorted(set(labels) - set(images))

        for stem in missing_label_stems:
            issues.append(
                _issue(
                    split,
                    "missing_label",
                    images[stem],
                    dataset_path,
                    "Image does not have a matching label file.",
                )
            )
            boxes_per_image.append(
                {
                    "split": split,
                    "image": _relative(images[stem], dataset_path),
                    "box_count": 0,
                }
            )

        for stem in orphan_label_stems:
            issues.append(
                _issue(
                    split,
                    "orphan_label",
                    labels[stem],
                    dataset_path,
                    "Label file does not have a matching image.",
                )
            )

        split_box_count = 0
        empty_label_count = 0
        for stem in sorted(set(images) & set(labels)):
            box_count, file_classes, file_issues = _parse_label_file(
                labels[stem], split, dataset_path
            )
            split_box_count += box_count
            class_distribution.update(file_classes)
            issues.extend(file_issues)
            if any(issue["type"] == "empty_label" for issue in file_issues):
                empty_label_count += 1
            boxes_per_image.append(
                {
                    "split": split,
                    "image": _relative(images[stem], dataset_path),
                    "box_count": box_count,
                }
            )

        split_stats[split] = {
            "image_count": len(images),
            "label_count": len(labels),
            "missing_label_count": len(missing_label_stems),
            "orphan_label_count": len(orphan_label_stems),
            "empty_label_count": empty_label_count,
            "box_count": split_box_count,
        }

    issue_counts = Counter(issue["type"] for issue in issues)
    total_images = sum(stats["image_count"] for stats in split_stats.values())
    total_labels = sum(stats["label_count"] for stats in split_stats.values())
    total_boxes = sum(stats["box_count"] for stats in split_stats.values())

    return {
        "dataset_path": dataset_path.as_posix(),
        "scanned_at": datetime.now().isoformat(timespec="seconds"),
        "overview": {
            "total_images": total_images,
            "total_label_files": total_labels,
            "total_boxes": total_boxes,
            "total_issues": len(issues),
        },
        "splits": split_stats,
        "class_distribution": dict(sorted(class_distribution.items())),
        "boxes_per_image": sorted(
            boxes_per_image, key=lambda item: (item["split"], item["image"])
        ),
        "issue_counts": dict(sorted(issue_counts.items())),
        "issues": issues,
    }


def summarize_yolo_dataset(dataset_dir: str | Path) -> dict[str, Any]:
    """Backward-compatible wrapper for the YOLO dataset audit."""
    return audit_yolo_dataset(dataset_dir)
