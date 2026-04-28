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


def _best_record(
    records: list[dict[str, Any]],
    metric_name: str,
) -> dict[str, Any] | None:
    """Return the record with the highest value for a metric."""
    valid_records = [
        record for record in records if record.get(metric_name) is not None
    ]
    if not valid_records:
        return None
    return max(valid_records, key=lambda record: float(record.get(metric_name, 0)))


def _experiment_summary_lines(
    record: dict[str, Any] | None,
    metric_name: str,
) -> list[str]:
    """Build Chinese summary lines for the best experiment."""
    if not record:
        return ["- 暂无可用实验记录。"]
    value = record.get(metric_name)
    metric_labels = {
        "precision": "precision",
        "recall": "recall",
        "map50": "mAP50",
    }
    metric_label = metric_labels.get(metric_name, metric_name)
    return [
        f"- 实验名称：{record.get('experiment_name', '')}",
        f"- {metric_label}：{float(value):.4f}",
        f"- 模型：{record.get('model_name', '')}",
        f"- 数据集：{record.get('dataset_name', '')}",
    ]


def _diagnose_experiments(records: list[dict[str, Any]]) -> list[str]:
    """Create simple conclusions from experiment records."""
    conclusions: list[str] = []
    if len(records) < 2:
        return ["实验数量较少，建议继续补充实验记录后再做趋势判断。"]

    ordered_records = sorted(
        records,
        key=lambda record: str(record.get("created_at", "")),
    )
    first = ordered_records[0]
    last = ordered_records[-1]

    first_recall = float(first.get("recall") or 0)
    last_recall = float(last.get("recall") or 0)
    first_precision = float(first.get("precision") or 0)
    last_precision = float(last.get("precision") or 0)

    if last_recall > first_recall and last_precision < first_precision:
        conclusions.append(
            "recall 提升但 precision 下降，说明模型可能更偏向高召回策略，后续需要结合误检样本进一步分析。"
        )
    if last_precision > first_precision and last_recall < first_recall:
        conclusions.append(
            "precision 提升但 recall 下降，说明模型可能更保守，后续需要重点关注漏检样本。"
        )

    best_map50 = _best_record(records, "map50")
    if best_map50:
        map50 = float(best_map50.get("map50") or 0)
        map50_95 = float(best_map50.get("map50_95") or 0)
        if map50 - map50_95 >= 0.2:
            conclusions.append(
                "mAP50 与 mAP50-95 差距较大，说明目标定位质量仍有优化空间。"
            )

    if len(records) < 3:
        conclusions.append("实验数量较少，建议继续补充实验记录后再做趋势判断。")
    if not conclusions:
        conclusions.append("当前实验记录可以用于基础对比，建议继续结合样本级误差分析。")

    return conclusions


def generate_experiment_report(
    records: list[dict[str, Any]],
    output_path: str | Path = "reports/experiment_report.md",
) -> Path:
    """Write a Chinese Markdown report for experiment tracking records."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    table_rows = [
        [
            record.get("experiment_name", ""),
            record.get("dataset_name", ""),
            record.get("model_name", ""),
            record.get("imgsz", ""),
            record.get("batch", ""),
            record.get("epochs", ""),
            record.get("precision", ""),
            record.get("recall", ""),
            record.get("map50", ""),
            record.get("map50_95", ""),
            record.get("created_at", ""),
        ]
        for record in records
    ] or [["-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"]]

    generated_at = datetime.now().isoformat(timespec="seconds")
    best_recall = _best_record(records, "recall")
    best_precision = _best_record(records, "precision")
    best_map50 = _best_record(records, "map50")

    lines = [
        "# 实验追踪报告",
        "",
        f"- 生成时间：`{generated_at}`",
        f"- 实验总数：`{len(records)}`",
        "",
        "## 实验记录表",
        "",
        _markdown_table(
            [
                "实验名称",
                "数据集",
                "模型",
                "输入尺寸",
                "batch",
                "训练轮数",
                "precision",
                "recall",
                "mAP50",
                "mAP50-95",
                "创建时间",
            ],
            table_rows,
        ),
        "",
        "## 最佳召回率实验",
        "",
        *_experiment_summary_lines(best_recall, "recall"),
        "",
        "## 最佳精确率实验",
        "",
        *_experiment_summary_lines(best_precision, "precision"),
        "",
        "## 最佳 mAP50 实验",
        "",
        *_experiment_summary_lines(best_map50, "map50"),
        "",
        "## 简单诊断结论",
        "",
        *[f"- {item}" for item in _diagnose_experiments(records)],
        "",
    ]

    output.write_text("\n".join(lines), encoding="utf-8")
    return output
