"""Streamlit entry point for cv-debug-lab."""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.dataset_auditor import audit_yolo_dataset
from src.report_generator import generate_dataset_audit_report


DEFAULT_DATASET_PATH = Path("example_data/yolo_demo")
DEFAULT_REPORT_PATH = Path("reports/dataset_audit_report.md")
ISSUE_DESCRIPTIONS = {
    "missing_label": "图片缺少对应标签",
    "orphan_label": "标签缺少对应图片",
    "empty_label": "空标签文件",
    "bbox_out_of_bounds": "bbox 越界",
    "invalid_bbox_size": "bbox 宽高非法",
    "invalid_label_format": "标签格式非法",
}


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
        st.dataframe(split_df, use_container_width=True)

        st.subheader("类别分布")
        class_rows = [
            {"类别 ID": class_id, "目标框数量": count}
            for class_id, count in audit_result["class_distribution"].items()
        ]
        st.dataframe(pd.DataFrame(class_rows), use_container_width=True)

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
        st.dataframe(issue_df, use_container_width=True)

        st.subheader("每张图片目标框数量")
        boxes_df = pd.DataFrame(audit_result["boxes_per_image"]).rename(
            columns={
                "split": "数据划分",
                "image": "图片路径",
                "box_count": "目标框数量",
            }
        )
        st.dataframe(boxes_df, use_container_width=True)

        st.success(f"报告已生成：{report_path.as_posix()}")


if __name__ == "__main__":
    main()
