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
        record for record in records if record.get(metric_name) not in (None, "")
    ]
    if not valid_records:
        return None
    return max(valid_records, key=lambda record: _safe_float(record.get(metric_name)))


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


def _safe_int(value: Any, default: int = 0) -> int:
    """Convert a value to int without raising for missing report fields."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float without raising for missing report fields."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _record_name(record: dict[str, Any] | None) -> str:
    """Return an experiment display name."""
    if not record:
        return "暂无"
    return str(record.get("experiment_name") or "未命名实验")


def _recent_experiment(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the most recent experiment by created_at."""
    if not records:
        return None
    return max(records, key=lambda record: str(record.get("created_at", "")))


def _cv_debug_conclusions(
    dataset_audit_result: dict[str, Any],
    experiments: list[dict[str, Any]],
) -> list[str]:
    """Create cross-module diagnosis conclusions."""
    conclusions: list[str] = []
    overview = dataset_audit_result.get("overview", {})
    issue_counts = dataset_audit_result.get("issue_counts", {})
    total_labels = max(_safe_int(overview.get("total_label_files")), 1)
    empty_labels = _safe_int(issue_counts.get("empty_label"))

    missing_or_orphan = _safe_int(issue_counts.get("missing_label")) + _safe_int(
        issue_counts.get("orphan_label")
    )
    invalid_boxes = _safe_int(issue_counts.get("bbox_out_of_bounds")) + _safe_int(
        issue_counts.get("invalid_bbox_size")
    )

    if missing_or_orphan > 0:
        conclusions.append(
            "数据集结构存在不一致问题，建议在训练前优先修复图片与标签匹配关系。"
        )
    if invalid_boxes > 0:
        conclusions.append(
            "标注质量存在异常框问题，可能影响模型训练稳定性和评估可信度。"
        )
    if empty_labels / total_labels >= 0.2:
        conclusions.append(
            "空标签样本比例较高，需要确认这些样本是否确实为负样本，避免误伤召回率。"
        )

    best_recall = _best_record(experiments, "recall")
    best_precision = _best_record(experiments, "precision")
    best_map50 = _best_record(experiments, "map50")

    if len(experiments) < 2:
        conclusions.append(
            "当前实验记录较少，暂不适合做趋势判断，建议继续补充实验记录。"
        )
    if (
        best_recall
        and best_precision
        and best_recall.get("experiment_name") != best_precision.get("experiment_name")
    ):
        conclusions.append(
            "当前实验中 recall 和 precision 最优结果来自不同实验，说明模型在召回和误检之间存在权衡，需要结合错例分析进一步判断。"
        )
    if best_recall and _safe_float(best_recall.get("recall")) < 0.7:
        conclusions.append(
            "当前模型召回率仍有提升空间，建议优先分析漏检样本和小目标样本。"
        )
    if best_precision and _safe_float(best_precision.get("precision")) < 0.7:
        conclusions.append(
            "当前模型误检压力较大，建议结合 FP 样本、阈值和 NMS 策略继续分析。"
        )
    if best_map50 and _safe_float(best_map50.get("map50")) < 0.7:
        conclusions.append(
            "当前 mAP50 仍有提升空间，建议结合数据质量和训练配置继续迭代。"
        )

    if not conclusions:
        conclusions.append(
            "当前数据集和实验记录已具备基础复盘价值，可以继续补充错例分析和可视化结果。"
        )
    return conclusions


def _cv_debug_next_steps(
    dataset_audit_result: dict[str, Any],
    experiments: list[dict[str, Any]],
) -> list[str]:
    """Create next-step suggestions from cross-module diagnosis inputs."""
    issue_counts = dataset_audit_result.get("issue_counts", {})
    suggestions: list[str] = []

    if _safe_int(issue_counts.get("missing_label")) + _safe_int(
        issue_counts.get("orphan_label")
    ) > 0:
        suggestions.append("修复数据集结构问题，确保图片和标签一一对应。")
    if _safe_int(issue_counts.get("bbox_out_of_bounds")) + _safe_int(
        issue_counts.get("invalid_bbox_size")
    ) > 0:
        suggestions.append("检查异常 bbox 标注，优先处理越界框和宽高非法框。")
    if _safe_int(issue_counts.get("empty_label")) > 0:
        suggestions.append("确认空标签是否为真实负样本。")
    if len(experiments) < 2:
        suggestions.append("增加实验记录，至少保留两组以上可对比实验。")

    suggestions.extend(
        [
            "做误检漏检分析，拆分 FP/FN 样本原因。",
            "做阈值/NMS 扫描，观察 precision 与 recall 的权衡。",
            "补充 hard case 样本，提升模型对困难场景的鲁棒性。",
            "生成 GitHub 展示截图，补充项目使用效果说明。",
        ]
    )

    deduped: list[str] = []
    for item in suggestions:
        if item not in deduped:
            deduped.append(item)
    return deduped


def generate_cv_debug_report(
    dataset_audit_result: dict[str, Any],
    experiments: list[dict[str, Any]],
    output_path: str | Path = "reports/cv_debug_report.md",
) -> Path:
    """Generate a combined Chinese CV training diagnosis report."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now().isoformat(timespec="seconds")
    overview = dataset_audit_result.get("overview", {})
    splits = dataset_audit_result.get("splits", {})
    issue_counts = dataset_audit_result.get("issue_counts", {})
    class_distribution = dataset_audit_result.get("class_distribution", {})
    train_stats = splits.get("train", {})
    val_stats = splits.get("val", {})

    best_recall = _best_record(experiments, "recall")
    best_precision = _best_record(experiments, "precision")
    best_map50 = _best_record(experiments, "map50")
    recent = _recent_experiment(experiments)
    empty_labels = _safe_int(train_stats.get("empty_label_count")) + _safe_int(
        val_stats.get("empty_label_count")
    )
    missing_labels = _safe_int(train_stats.get("missing_label_count")) + _safe_int(
        val_stats.get("missing_label_count")
    )
    orphan_labels = _safe_int(train_stats.get("orphan_label_count")) + _safe_int(
        val_stats.get("orphan_label_count")
    )

    class_rows = [
        [class_id, count] for class_id, count in class_distribution.items()
    ] or [["-", 0]]

    experiment_rows = [
        ["最佳 recall 实验", _record_name(best_recall), f"{_safe_float(best_recall.get('recall') if best_recall else None):.4f}" if best_recall else "-"],
        ["最佳 precision 实验", _record_name(best_precision), f"{_safe_float(best_precision.get('precision') if best_precision else None):.4f}" if best_precision else "-"],
        ["最佳 mAP50 实验", _record_name(best_map50), f"{_safe_float(best_map50.get('map50') if best_map50 else None):.4f}" if best_map50 else "-"],
        ["最近一次实验", _record_name(recent), str(recent.get("created_at", "")) if recent else "-"],
    ]

    lines = [
        "# CV 训练诊断报告",
        "",
        "## 报告概览",
        "",
        _markdown_table(
            ["项目", "数值"],
            [
                ["生成时间", generated_at],
                ["数据集路径", dataset_audit_result.get("dataset_path", "")],
                ["实验记录数量", len(experiments)],
                ["总图片数", overview.get("total_images", 0)],
                ["总目标框数", overview.get("total_boxes", 0)],
                ["总问题数量", overview.get("total_issues", 0)],
            ],
        ),
        "",
        "## 数据集体检摘要",
        "",
        _markdown_table(
            ["指标", "数值"],
            [
                ["train 图片数", train_stats.get("image_count", 0)],
                ["val 图片数", val_stats.get("image_count", 0)],
                ["标签文件数", overview.get("total_label_files", 0)],
                ["空标签文件数", empty_labels],
                ["bbox 越界数量", issue_counts.get("bbox_out_of_bounds", 0)],
                ["bbox 宽高非法数量", issue_counts.get("invalid_bbox_size", 0)],
                ["图片缺标签数量", missing_labels],
                ["标签缺图片数量", orphan_labels],
            ],
        ),
        "",
        "### 类别分布摘要",
        "",
        _markdown_table(["类别 ID", "目标框数量"], class_rows),
        "",
        "## 实验追踪摘要",
        "",
        _markdown_table(["摘要项", "实验名称", "指标/时间"], experiment_rows),
        "",
        "## 自动诊断结论",
        "",
        *[
            f"- {conclusion}"
            for conclusion in _cv_debug_conclusions(dataset_audit_result, experiments)
        ],
        "",
        "## 下一步建议",
        "",
        *[
            f"- {suggestion}"
            for suggestion in _cv_debug_next_steps(dataset_audit_result, experiments)
        ],
        "",
    ]

    output.write_text("\n".join(lines), encoding="utf-8")
    return output
