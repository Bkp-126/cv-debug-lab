"""Markdown report generation helpers for cv-debug-lab."""

from datetime import datetime
from pathlib import Path
from typing import Any


def build_markdown_report(title: str, output_path: str | Path) -> dict[str, str]:
    """Return placeholder metadata for a future Markdown report."""
    return {
        "title": title,
        "output_path": str(Path(output_path)),
        "status": "not_generated",
    }


def _markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    """Build a simple Markdown table."""
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = [
        "| " + " | ".join(str(value) for value in row) + " |" for row in rows
    ]
    return "\n".join([header_line, separator, *row_lines])


def _diagnose(audit_result: dict[str, Any]) -> list[str]:
    """Create simple engineering conclusions from audit statistics."""
    conclusions: list[str] = []
    issue_counts = audit_result.get("issue_counts", {})
    overview = audit_result.get("overview", {})
    splits = audit_result.get("splits", {})

    if issue_counts.get("bbox_out_of_bounds", 0) > 0:
        conclusions.append("检测到 bbox 越界问题，建议优先检查相关标注文件。")
    if issue_counts.get("invalid_bbox_size", 0) > 0:
        conclusions.append("检测到 bbox 宽高非法问题，建议修复异常标签后再训练。")

    total_labels = max(int(overview.get("total_label_files", 0)), 1)
    empty_labels = int(issue_counts.get("empty_label", 0))
    if empty_labels / total_labels >= 0.2:
        conclusions.append(
            "检测到空标签文件，需要确认这些图片是否确实为负样本。"
        )

    train_images = int(splits.get("train", {}).get("image_count", 0))
    val_images = int(splits.get("val", {}).get("image_count", 0))
    total_images = train_images + val_images
    if total_images > 0:
        train_ratio = train_images / total_images
        if train_ratio < 0.5 or train_ratio > 0.9:
            conclusions.append(
                "train/val 划分比例不够均衡，建议检查数据集划分策略。"
            )

    if issue_counts.get("missing_label", 0) > 0 or issue_counts.get("orphan_label", 0) > 0:
        conclusions.append(
            "检测到图片和标签不匹配，建议修复数据集目录结构后再训练。"
        )

    if not conclusions:
        conclusions.append("本次体检未发现明显阻塞问题，可以进入下一步实验追踪和训练结果分析。")
    else:
        conclusions.append("如果问题较少且已确认原因，可以进入下一步实验追踪和训练结果分析。")

    return conclusions


def generate_dataset_audit_report(
    audit_result: dict[str, Any],
    output_path: str | Path = "reports/dataset_audit_report.md",
) -> Path:
    """Write a Markdown report from a dataset audit result."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    overview = audit_result.get("overview", {})
    splits = audit_result.get("splits", {})
    class_distribution = audit_result.get("class_distribution", {})
    issue_counts = audit_result.get("issue_counts", {})
    issues = audit_result.get("issues", [])
    issue_descriptions = {
        "missing_label": "图片缺少对应标签",
        "orphan_label": "标签缺少对应图片",
        "empty_label": "空标签文件",
        "bbox_out_of_bounds": "bbox 越界",
        "invalid_bbox_size": "bbox 宽高非法",
        "invalid_label_format": "标签格式非法",
    }

    split_rows = [
        [
            split,
            stats.get("image_count", 0),
            stats.get("label_count", 0),
            stats.get("box_count", 0),
            stats.get("empty_label_count", 0),
            stats.get("missing_label_count", 0),
            stats.get("orphan_label_count", 0),
        ]
        for split, stats in splits.items()
    ]
    class_rows = [
        [class_id, count] for class_id, count in class_distribution.items()
    ] or [["-", 0]]
    issue_count_rows = [
        [issue_type, issue_descriptions.get(issue_type, "未分类问题"), count]
        for issue_type, count in issue_counts.items()
    ] or [["-", "-", 0]]
    issue_rows = [
        [
            item.get("split", ""),
            item.get("type", ""),
            issue_descriptions.get(item.get("type", ""), "未分类问题"),
            item.get("path", ""),
            item.get("line", ""),
        ]
        for item in issues
    ] or [["-", "-", "-", "-", "未发现问题。"]]

    generated_at = datetime.now().isoformat(timespec="seconds")
    lines = [
        "# 数据集体检报告",
        "",
        f"- 数据集路径：`{audit_result.get('dataset_path', '')}`",
        f"- 扫描时间：`{audit_result.get('scanned_at', generated_at)}`",
        f"- 报告生成时间：`{generated_at}`",
        "",
        "## 总览统计",
        "",
        _markdown_table(
            ["指标", "数值"],
            [
                ["图片总数", overview.get("total_images", 0)],
                ["标签文件总数", overview.get("total_label_files", 0)],
                ["目标框总数", overview.get("total_boxes", 0)],
                ["问题总数", overview.get("total_issues", 0)],
            ],
        ),
        "",
        "## train/val 分布",
        "",
        _markdown_table(
            [
                "数据划分",
                "图片数量",
                "标签文件数量",
                "目标框数量",
                "空标签数量",
                "图片缺标签数量",
                "标签缺图片数量",
            ],
            split_rows,
        ),
        "",
        "## 类别分布",
        "",
        _markdown_table(["类别 ID", "目标框数量"], class_rows),
        "",
        "## 问题统计",
        "",
        _markdown_table(["问题类型", "中文解释", "数量"], issue_count_rows),
        "",
        "## 问题样本清单",
        "",
        _markdown_table(["数据划分", "问题类型", "中文解释", "文件路径", "行号"], issue_rows),
        "",
        "## 诊断结论",
        "",
        *[f"- {item}" for item in _diagnose(audit_result)],
        "",
    ]

    output.write_text("\n".join(lines), encoding="utf-8")
    return output
