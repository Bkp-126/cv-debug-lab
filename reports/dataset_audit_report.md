# 数据集体检报告

- 数据集路径：`example_data/yolo_demo`
- 扫描时间：`2026-04-28T16:49:28`
- 报告生成时间：`2026-04-28T16:49:28`

## 总览统计

| 指标 | 数值 |
| --- | --- |
| 图片总数 | 10 |
| 标签文件总数 | 10 |
| 目标框总数 | 7 |
| 问题总数 | 10 |

## train/val 分布

| 数据划分 | 图片数量 | 标签文件数量 | 目标框数量 | 空标签数量 | 图片缺标签数量 | 标签缺图片数量 |
| --- | --- | --- | --- | --- | --- | --- |
| train | 6 | 6 | 5 | 1 | 1 | 1 |
| val | 4 | 4 | 2 | 1 | 1 | 1 |

## 类别分布

| 类别 ID | 目标框数量 |
| --- | --- |
| 0 | 3 |
| 1 | 3 |
| 2 | 1 |

## 问题统计

| 问题类型 | 中文解释 | 数量 |
| --- | --- | --- |
| bbox_out_of_bounds | bbox 越界 | 2 |
| empty_label | 空标签文件 | 2 |
| invalid_bbox_size | bbox 宽高非法 | 2 |
| missing_label | 图片缺少对应标签 | 2 |
| orphan_label | 标签缺少对应图片 | 2 |

## 问题样本清单

| 数据划分 | 问题类型 | 中文解释 | 文件路径 | 行号 |
| --- | --- | --- | --- | --- |
| train | missing_label | 图片缺少对应标签 | images/train/train_006.jpg |  |
| train | orphan_label | 标签缺少对应图片 | labels/train/train_orphan.txt |  |
| train | empty_label | 空标签文件 | labels/train/train_003.txt |  |
| train | bbox_out_of_bounds | bbox 越界 | labels/train/train_004.txt | 1 |
| train | invalid_bbox_size | bbox 宽高非法 | labels/train/train_005.txt | 1 |
| train | bbox_out_of_bounds | bbox 越界 | labels/train/train_005.txt | 1 |
| val | missing_label | 图片缺少对应标签 | images/val/val_004.jpg |  |
| val | orphan_label | 标签缺少对应图片 | labels/val/val_orphan.txt |  |
| val | empty_label | 空标签文件 | labels/val/val_002.txt |  |
| val | invalid_bbox_size | bbox 宽高非法 | labels/val/val_003.txt | 1 |

## 诊断结论

- 检测到 bbox 越界问题，建议优先检查相关标注文件。
- 检测到 bbox 宽高非法问题，建议修复异常标签后再训练。
- 检测到空标签文件，需要确认这些图片是否确实为负样本。
- 检测到图片和标签不匹配，建议修复数据集目录结构后再训练。
- 如果问题较少且已确认原因，可以进入下一步实验追踪和训练结果分析。
