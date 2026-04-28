"""Streamlit entry point for cv-debug-lab."""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.dataset_auditor import audit_yolo_dataset
from src.experiment_tracker import (
    add_experiment,
    init_db,
    list_experiments,
    parse_yolo_results_csv,
    seed_demo_experiments,
)
from src.report_generator import (
    generate_cv_debug_report,
    generate_dataset_audit_report,
    generate_experiment_report,
)


DEFAULT_DATASET_PATH = Path("example_data/yolo_demo")
DEFAULT_REPORT_PATH = Path("reports/dataset_audit_report.md")
DEFAULT_DB_PATH = Path("data/experiments.db")
DEFAULT_EXPERIMENT_REPORT_PATH = Path("reports/experiment_report.md")
DEFAULT_CV_DEBUG_REPORT_PATH = Path("reports/cv_debug_report.md")
ISSUE_DESCRIPTIONS = {
    "missing_label": "图片缺少对应标签",
    "orphan_label": "标签缺少对应图片",
    "empty_label": "空标签文件",
    "bbox_out_of_bounds": "bbox 越界",
    "invalid_bbox_size": "bbox 宽高非法",
    "invalid_label_format": "标签格式非法",
}
EXPERIMENT_DISPLAY_COLUMNS = {
    "experiment_id": "实验 ID",
    "experiment_name": "实验名称",
    "dataset_name": "数据集",
    "model_name": "模型",
    "checkpoint_path": "权重路径",
    "imgsz": "输入尺寸",
    "batch": "单批样本数",
    "epochs": "训练轮数",
    "precision": "精确率",
    "recall": "召回率",
    "map50": "mAP50",
    "map50_95": "mAP50-95",
    "notes": "备注",
    "created_at": "创建时间",
}
METRIC_LABELS = {
    "precision": "精确率",
    "recall": "召回率",
    "map50": "mAP50",
}


def _best_experiment(records: list[dict], metric_name: str) -> dict | None:
    """Return the best experiment record for a metric."""
    valid_records = [
        record for record in records if record.get(metric_name) is not None
    ]
    if not valid_records:
        return None
    return max(valid_records, key=lambda record: float(record.get(metric_name, 0)))


def _show_best_metric(records: list[dict], metric_name: str, label: str) -> None:
    """Display the best experiment for a metric."""
    best = _best_experiment(records, metric_name)
    if not best:
        st.info(f"暂无可用的 {label} 指标。")
        return
    title = f"最佳 {label} 实验" if label.startswith("mAP") else f"最佳{label}实验"
    metric_label = {
        "precision": "precision",
        "recall": "recall",
        "map50": "mAP50",
    }.get(metric_name, metric_name)
    st.write(
        f"{title}：`{best['experiment_name']}`，"
        f"{metric_label}={float(best[metric_name]):.4f}"
    )


def _best_metric_text(records: list[dict], metric_name: str) -> str:
    """Return a compact best-metric text for the combined report area."""
    best = _best_experiment(records, metric_name)
    if not best:
        return "暂无实验记录"
    metric_label = {
        "precision": "precision",
        "recall": "recall",
        "map50": "mAP50",
    }.get(metric_name, metric_name)
    return f"{best['experiment_name']}，{metric_label}={float(best[metric_name]):.4f}"


def main() -> None:
    """Render the cv-debug-lab V0.1 home page."""
    st.set_page_config(
        page_title="cv-debug-lab",
        layout="wide",
    )

    st.title("cv-debug-lab")
    st.write("面向计算机视觉训练流程的轻量级诊断工具箱")

    st.divider()

    st.header("功能模块")
    columns = st.columns(3)
    modules = [
        (
            "数据集体检",
            "扫描 YOLO 数据集结构、标签文件、类别分布和常见标注问题。",
        ),
        (
            "实验追踪",
            "记录训练轮次、指标、备注和轻量级实验元数据。",
        ),
        (
            "报告生成",
            "生成便于复盘的数据集体检和训练诊断 Markdown 报告。",
        ),
    ]

    for column, (name, description) in zip(columns, modules):
        with column:
            st.subheader(name)
            st.write(description)

    st.header("V0.1 Roadmap")
    st.markdown(
        """
- 完成 Streamlit 首页和基础交互。
- 支持 YOLO 数据集结构检查。
- 解析示例训练指标文件 `results.csv`。
- 后续使用 SQLite 管理实验记录。
- 导出 Markdown 报告用于本地复盘。
"""
    )

    st.divider()

    st.header("数据集体检")
    st.write("默认数据集路径")
    st.code(DEFAULT_DATASET_PATH.as_posix(), language="text")

    if st.button("运行数据集体检"):
        audit_result = audit_yolo_dataset(DEFAULT_DATASET_PATH)
        report_path = generate_dataset_audit_report(
            audit_result, DEFAULT_REPORT_PATH
        )

        st.subheader("数据集总览")
        overview = audit_result["overview"]
        metric_columns = st.columns(4)
        metric_columns[0].metric("图片总数", overview["total_images"])
        metric_columns[1].metric("标签文件数", overview["total_label_files"])
        metric_columns[2].metric("目标框总数", overview["total_boxes"])
        metric_columns[3].metric("问题总数", overview["total_issues"])

        st.subheader("train/val 分布")
        split_rows = [
            {"split": split, **stats}
            for split, stats in audit_result["splits"].items()
        ]
        split_df = pd.DataFrame(split_rows).rename(
            columns={
                "split": "数据划分",
                "image_count": "图片数量",
                "label_count": "标签文件数量",
                "missing_label_count": "图片缺标签数量",
                "orphan_label_count": "标签缺图片数量",
                "empty_label_count": "空标签数量",
                "box_count": "目标框数量",
            }
        )
        st.dataframe(split_df, width="stretch")

        st.subheader("类别分布")
        class_rows = [
            {"类别 ID": class_id, "目标框数量": count}
            for class_id, count in audit_result["class_distribution"].items()
        ]
        st.dataframe(pd.DataFrame(class_rows), width="stretch")

        st.subheader("数据集问题清单")
        issue_df = pd.DataFrame(audit_result["issues"])
        if not issue_df.empty:
            issue_df["问题说明"] = issue_df["type"].map(
                lambda value: ISSUE_DESCRIPTIONS.get(value, "未分类问题")
            )
            issue_df = issue_df.rename(
                columns={
                    "split": "数据划分",
                    "type": "问题类型",
                    "path": "文件路径",
                    "line": "行号",
                }
            )
            issue_df = issue_df[
                ["数据划分", "问题类型", "问题说明", "文件路径", "行号"]
            ]
        st.dataframe(issue_df, width="stretch")

        st.subheader("每张图片目标框数量")
        boxes_df = pd.DataFrame(audit_result["boxes_per_image"]).rename(
            columns={
                "split": "数据划分",
                "image": "图片路径",
                "box_count": "目标框数量",
            }
        )
        st.dataframe(boxes_df, width="stretch")

        st.success(f"报告已生成：{report_path.as_posix()}")

    st.divider()

    st.header("实验追踪")
    st.write(
        "用于记录模型训练参数和指标，帮助对比不同实验的 precision、recall、mAP 等结果。"
    )
    init_db(DEFAULT_DB_PATH)
    st.caption(f"本地 SQLite 数据库：{DEFAULT_DB_PATH.as_posix()}")

    if st.button("加载示例实验记录"):
        inserted = seed_demo_experiments(DEFAULT_DB_PATH)
        if inserted:
            st.success(f"已加载 {inserted} 条示例实验记录。")
        else:
            st.info("示例实验记录已存在，无需重复加载。")

    st.subheader("解析 YOLO results.csv")
    uploaded_file = st.file_uploader(
        "上传 YOLO results.csv",
        type=["csv"],
        help="将提取最后一行的 precision、recall、mAP50、mAP50-95。",
    )
    parsed_metrics = st.session_state.get("parsed_metrics", {})
    if uploaded_file is not None:
        try:
            uploaded_file.seek(0)
            parsed_metrics = parse_yolo_results_csv(uploaded_file)
            st.session_state["parsed_metrics"] = parsed_metrics
            st.success("results.csv 解析成功。")
            parsed_df = pd.DataFrame([parsed_metrics]).rename(
                columns={
                    "precision": "精确率",
                    "recall": "召回率",
                    "map50": "mAP50",
                    "map50_95": "mAP50-95",
                }
            )
            st.dataframe(
                parsed_df,
                width="stretch",
            )
        except ValueError as exc:
            st.error(str(exc))

    st.subheader("新增实验记录")
    with st.form("experiment_form"):
        left_column, right_column = st.columns(2)
        with left_column:
            experiment_name = st.text_input("实验名称", value="demo_experiment")
            dataset_name = st.text_input("数据集名称", value="yolo_demo")
            model_name = st.text_input("模型名称", value="yolo11n")
            checkpoint_path = st.text_input(
                "权重路径",
                value="example_weights/yolo11n_demo_best.pt",
            )
            imgsz = st.number_input("输入尺寸 `imgsz`", min_value=1, value=640, step=32)
            batch = st.number_input("`batch size`", min_value=1, value=16, step=1)
        with right_column:
            epochs = st.number_input("训练轮数 `epochs`", min_value=1, value=50, step=1)
            precision = st.number_input(
                "精确率 `precision`",
                min_value=0.0,
                max_value=1.0,
                value=float(parsed_metrics.get("precision", 0.0)),
                step=0.001,
                format="%.4f",
            )
            recall = st.number_input(
                "召回率 `recall`",
                min_value=0.0,
                max_value=1.0,
                value=float(parsed_metrics.get("recall", 0.0)),
                step=0.001,
                format="%.4f",
            )
            map50 = st.number_input(
                "mAP50",
                min_value=0.0,
                max_value=1.0,
                value=float(parsed_metrics.get("map50", 0.0)),
                step=0.001,
                format="%.4f",
            )
            map50_95 = st.number_input(
                "mAP50-95",
                min_value=0.0,
                max_value=1.0,
                value=float(parsed_metrics.get("map50_95", 0.0)),
                step=0.001,
                format="%.4f",
            )
        notes = st.text_area("备注", value="本次实验记录用于本地对比。")
        submitted = st.form_submit_button("保存实验记录")

    if submitted:
        try:
            add_experiment(
                DEFAULT_DB_PATH,
                {
                    "experiment_name": experiment_name,
                    "dataset_name": dataset_name,
                    "model_name": model_name,
                    "checkpoint_path": checkpoint_path,
                    "imgsz": int(imgsz),
                    "batch": int(batch),
                    "epochs": int(epochs),
                    "precision": float(precision),
                    "recall": float(recall),
                    "map50": float(map50),
                    "map50_95": float(map50_95),
                    "notes": notes,
                },
            )
            st.success("实验记录已保存。")
        except ValueError as exc:
            st.error(str(exc))

    experiment_records = list_experiments(DEFAULT_DB_PATH)
    st.subheader("实验记录表")
    display_columns = [
        "experiment_name",
        "dataset_name",
        "model_name",
        "checkpoint_path",
        "imgsz",
        "batch",
        "epochs",
        "precision",
        "recall",
        "map50",
        "map50_95",
        "notes",
        "created_at",
    ]
    experiment_df = (
        pd.DataFrame(experiment_records)[display_columns]
        if experiment_records
        else pd.DataFrame(columns=display_columns)
    )
    experiment_df = experiment_df.rename(columns=EXPERIMENT_DISPLAY_COLUMNS)
    st.dataframe(
        experiment_df,
        width="stretch",
    )

    st.subheader("简单实验结论")
    if len(experiment_records) < 2:
        st.info("当前实验数量较少，建议继续补充实验记录后再进行趋势判断。")
    else:
        _show_best_metric(experiment_records, "recall", "召回率")
        _show_best_metric(experiment_records, "precision", "精确率")
        _show_best_metric(experiment_records, "map50", "mAP50")

    if st.button("生成实验追踪报告"):
        experiment_report_path = generate_experiment_report(
            experiment_records,
            DEFAULT_EXPERIMENT_REPORT_PATH,
        )
        st.success(f"报告已生成：{experiment_report_path.as_posix()}")

    st.divider()

    st.header("总诊断报告")
    st.write(
        "汇总数据集体检和实验追踪结果，生成一份适合复盘和展示的 CV 训练诊断报告。"
    )

    if st.button("生成总诊断报告"):
        if not DEFAULT_DATASET_PATH.exists():
            st.error(f"数据集路径不存在：{DEFAULT_DATASET_PATH.as_posix()}")
        else:
            cv_audit_result = audit_yolo_dataset(DEFAULT_DATASET_PATH)
            cv_experiment_records = list_experiments(DEFAULT_DB_PATH)
            if not cv_experiment_records:
                st.warning("当前没有实验记录，请先加载示例实验记录或手动新增实验记录。")

            cv_report_path = generate_cv_debug_report(
                cv_audit_result,
                cv_experiment_records,
                DEFAULT_CV_DEBUG_REPORT_PATH,
            )
            st.success(f"报告已生成：{cv_report_path.as_posix()}")

            st.subheader("关键诊断摘要")
            cv_overview = cv_audit_result.get("overview", {})
            summary_columns = st.columns(4)
            summary_columns[0].metric("图片总数", cv_overview.get("total_images", 0))
            summary_columns[1].metric("目标框总数", cv_overview.get("total_boxes", 0))
            summary_columns[2].metric("问题总数", cv_overview.get("total_issues", 0))
            summary_columns[3].metric("实验记录数", len(cv_experiment_records))

            st.write(f"最佳召回率实验：{_best_metric_text(cv_experiment_records, 'recall')}")
            st.write(
                f"最佳精确率实验：{_best_metric_text(cv_experiment_records, 'precision')}"
            )
            st.write(f"最佳 mAP50 实验：{_best_metric_text(cv_experiment_records, 'map50')}")


if __name__ == "__main__":
    main()
