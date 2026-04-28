"""Experiment tracking helpers for cv-debug-lab."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_YOLO_METRIC_COLUMNS = {
    "precision": "metrics/precision(B)",
    "recall": "metrics/recall(B)",
    "map50": "metrics/mAP50(B)",
    "map50_95": "metrics/mAP50-95(B)",
}

EXPERIMENT_COLUMNS = [
    "experiment_id",
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


def init_db(db_path: str | Path) -> Path:
    """Initialize the SQLite database and experiments table."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_name TEXT NOT NULL,
                dataset_name TEXT NOT NULL,
                model_name TEXT NOT NULL,
                checkpoint_path TEXT,
                imgsz INTEGER,
                batch INTEGER,
                epochs INTEGER,
                precision REAL,
                recall REAL,
                map50 REAL,
                map50_95 REAL,
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()

    return path


def add_experiment(db_path: str | Path, experiment_dict: dict[str, Any]) -> int:
    """Add one experiment record and return its generated experiment_id."""
    path = init_db(db_path)
    created_at = experiment_dict.get("created_at") or datetime.now().isoformat(
        timespec="seconds"
    )
    payload = {
        "experiment_name": str(experiment_dict.get("experiment_name") or "").strip(),
        "dataset_name": str(experiment_dict.get("dataset_name") or "").strip(),
        "model_name": str(experiment_dict.get("model_name") or "").strip(),
        "checkpoint_path": str(experiment_dict.get("checkpoint_path") or "").strip(),
        "imgsz": experiment_dict.get("imgsz"),
        "batch": experiment_dict.get("batch"),
        "epochs": experiment_dict.get("epochs"),
        "precision": experiment_dict.get("precision"),
        "recall": experiment_dict.get("recall"),
        "map50": experiment_dict.get("map50"),
        "map50_95": experiment_dict.get("map50_95"),
        "notes": str(experiment_dict.get("notes") or "").strip(),
        "created_at": created_at,
    }

    if not payload["experiment_name"]:
        raise ValueError("实验名称不能为空。")
    if not payload["dataset_name"]:
        raise ValueError("数据集名称不能为空。")
    if not payload["model_name"]:
        raise ValueError("模型名称不能为空。")

    with sqlite3.connect(path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO experiments (
                experiment_name,
                dataset_name,
                model_name,
                checkpoint_path,
                imgsz,
                batch,
                epochs,
                precision,
                recall,
                map50,
                map50_95,
                notes,
                created_at
            )
            VALUES (
                :experiment_name,
                :dataset_name,
                :model_name,
                :checkpoint_path,
                :imgsz,
                :batch,
                :epochs,
                :precision,
                :recall,
                :map50,
                :map50_95,
                :notes,
                :created_at
            )
            """,
            payload,
        )
        connection.commit()
        return int(cursor.lastrowid)


def list_experiments(db_path: str | Path) -> list[dict[str, Any]]:
    """Return all experiment records ordered by creation time."""
    path = init_db(db_path)
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                experiment_id,
                experiment_name,
                dataset_name,
                model_name,
                checkpoint_path,
                imgsz,
                batch,
                epochs,
                precision,
                recall,
                map50,
                map50_95,
                notes,
                created_at
            FROM experiments
            ORDER BY created_at DESC, experiment_id DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def parse_yolo_results_csv(csv_path: str | Path | Any) -> dict[str, float]:
    """Parse YOLO results.csv and return metrics from the last row."""
    try:
        dataframe = pd.read_csv(csv_path)
    except Exception as exc:
        raise ValueError(f"无法读取 YOLO results.csv：{exc}") from exc

    if dataframe.empty:
        raise ValueError("YOLO results.csv 为空，无法提取最后一行指标。")

    missing_columns = [
        column
        for column in REQUIRED_YOLO_METRIC_COLUMNS.values()
        if column not in dataframe.columns
    ]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"YOLO results.csv 缺少必要字段：{missing_text}")

    last_row = dataframe.iloc[-1]
    return {
        metric_name: float(last_row[column_name])
        for metric_name, column_name in REQUIRED_YOLO_METRIC_COLUMNS.items()
    }


def seed_demo_experiments(db_path: str | Path) -> int:
    """Insert demo experiment records when they do not already exist."""
    path = init_db(db_path)
    demo_records = [
        {
            "experiment_name": "demo_yolo11n_baseline",
            "dataset_name": "yolo_demo",
            "model_name": "yolo11n",
            "checkpoint_path": "example_weights/yolo11n_demo_best.pt",
            "imgsz": 640,
            "batch": 16,
            "epochs": 50,
            "precision": 0.721,
            "recall": 0.642,
            "map50": 0.688,
            "map50_95": 0.421,
            "notes": "轻量模型 baseline，用于快速验证训练流程。",
        },
        {
            "experiment_name": "demo_yolo11n_aug",
            "dataset_name": "yolo_demo",
            "model_name": "yolo11n",
            "checkpoint_path": "example_weights/yolo11n_demo_aug_best.pt",
            "imgsz": 640,
            "batch": 16,
            "epochs": 80,
            "precision": 0.698,
            "recall": 0.704,
            "map50": 0.731,
            "map50_95": 0.458,
            "notes": "增加基础数据增强，recall 有提升但 precision 略有下降。",
        },
        {
            "experiment_name": "demo_yolo11m_larger",
            "dataset_name": "yolo_demo",
            "model_name": "yolo11m",
            "checkpoint_path": "example_weights/yolo11m_demo_best.pt",
            "imgsz": 768,
            "batch": 8,
            "epochs": 80,
            "precision": 0.764,
            "recall": 0.681,
            "map50": 0.756,
            "map50_95": 0.493,
            "notes": "更大模型和更高输入分辨率，precision 与 mAP 有提升。",
        },
    ]

    inserted = 0
    with sqlite3.connect(path) as connection:
        existing_names = {
            row[0]
            for row in connection.execute(
                "SELECT experiment_name FROM experiments"
            ).fetchall()
        }

    for record in demo_records:
        if record["experiment_name"] in existing_names:
            continue
        add_experiment(path, record)
        inserted += 1

    return inserted


def initialize_experiment_store(db_path: str | Path) -> Path:
    """Backward-compatible wrapper for database initialization."""
    return init_db(db_path)


def record_experiment_note(note: str) -> dict[str, str]:
    """Return a lightweight note payload for compatibility with V0.1."""
    return {
        "note": note,
        "status": "not_persisted",
    }
