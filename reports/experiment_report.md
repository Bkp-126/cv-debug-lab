# 实验追踪报告

- 生成时间：`2026-04-28T17:02:01`
- 实验总数：`4`

## 实验记录表

| 实验名称 | 数据集 | 模型 | imgsz | batch | epochs | precision | recall | mAP50 | mAP50-95 | 创建时间 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| demo_experiment | yolo_demo | yolo11n | 640 | 16 | 50 | 0.721 | 0.642 | 0.688 | 0.421 | 2026-04-28T17:01:55 |
| demo_yolo11m_larger | yolo_demo | yolo11m | 768 | 8 | 80 | 0.764 | 0.681 | 0.756 | 0.493 | 2026-04-28T17:01:03 |
| demo_yolo11n_aug | yolo_demo | yolo11n | 640 | 16 | 80 | 0.698 | 0.704 | 0.731 | 0.458 | 2026-04-28T17:01:03 |
| demo_yolo11n_baseline | yolo_demo | yolo11n | 640 | 16 | 50 | 0.721 | 0.642 | 0.688 | 0.421 | 2026-04-28T17:01:03 |

## 最佳 recall 实验

- demo_yolo11n_aug，recall=0.7040，model=yolo11n，dataset=yolo_demo

## 最佳 precision 实验

- demo_yolo11m_larger，precision=0.7640，model=yolo11m，dataset=yolo_demo

## 最佳 mAP50 实验

- demo_yolo11m_larger，map50=0.7560，model=yolo11m，dataset=yolo_demo

## 简单诊断结论

- mAP50 表现高于 mAP50-95 较多，说明定位质量仍有优化空间。
