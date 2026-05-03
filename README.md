# cv-debug-lab

面向计算机视觉训练流程的轻量级诊断工具箱。

A lightweight debugging toolkit for computer vision training workflows.

## 简介

cv-debug-lab 是一个用 Python 和 Streamlit 构建的 CV 训练诊断小工具，适合在 YOLO/CV 项目中做训练前检查、训练后记录和结果复盘。

它把常见的工程排查动作整理成三个模块：数据集体检、实验追踪、总诊断报告。项目使用模拟 YOLO 数据集作为演示样例，可以直接本地运行，也可以作为个人算法工程作品展示。

## 为什么做

CV 训练效果不理想时，问题不一定只在模型本身。很多时候，数据结构、标签质量、训练划分和实验记录都会影响最终结果。

cv-debug-lab 关注这些训练流程中的基础环节：

- 图片和标签是否一一对应
- 标签文件是否为空
- bbox 是否越界或宽高非法
- train/val 数据划分是否清晰
- 类别分布是否明显异常
- 每次训练的 precision、recall、mAP 是否可追踪
- 训练结果是否能沉淀成可复盘报告

## 功能概览

### Dataset Auditor 数据集体检

- 扫描 YOLO 数据集目录
- 检查图片/标签匹配关系
- 统计空标签文件
- 检查 bbox 越界
- 检查 bbox 宽高非法
- 统计类别分布
- 统计每张图片目标框数量
- 生成中文数据集体检报告

### Experiment Tracker 实验追踪

- 手动新增实验记录
- 解析 YOLO `results.csv`
- 使用 SQLite 在本地保存实验记录
- 展示实验记录对比表
- 统计最佳 recall / precision / mAP50 实验
- 生成中文实验追踪报告

### Report Generator 总诊断报告

- 汇总数据集体检结果
- 汇总实验追踪结果
- 自动生成 CV 训练诊断报告
- 输出诊断结论和下一步建议

## 界面预览

截图建议放在 `screenshots/` 目录。当前版本预留以下截图位：

- 首页：`screenshots/home.png`
- 数据集体检：`screenshots/dataset_auditor.png`
- 实验追踪：`screenshots/experiment_tracker.png`
- 总诊断报告：`screenshots/summary_report.png`

## 快速开始

Windows PowerShell 示例：

```powershell
conda create -n cv-debug-lab python=3.11 -y
conda activate cv-debug-lab
pip install -r requirements.txt
streamlit run app.py
```

启动后可以依次体验：

- `运行数据集体检`
- `加载示例实验记录`
- `生成实验追踪报告`
- `生成总诊断报告`

## 示例数据

项目内置一份小型模拟 YOLO 数据集：

```text
example_data/yolo_demo/
  images/
    train/
    val/
  labels/
    train/
    val/
```

这份数据集用于演示数据集体检能力，覆盖了正常标签、空标签、bbox 越界、bbox 宽高非法、图片缺少标签、标签缺少图片等情况。

同时提供一份模拟训练结果：

```text
example_data/yolo_results/results.csv
```

用于演示 YOLO 指标解析，包括 precision、recall、mAP50 和 mAP50-95。

## 示例报告

运行页面功能后，会生成以下 Markdown 报告：

- `reports/dataset_audit_report.md`
- `reports/experiment_report.md`
- `reports/cv_debug_report.md`

其中 `reports/cv_debug_report.md` 是汇总报告，适合作为一次完整训练诊断的输出样例。

## 项目结构

```text
cv-debug-lab/
  app.py                         # Streamlit 应用入口
  src/
    dataset_auditor.py           # YOLO 数据集体检逻辑
    experiment_tracker.py        # 实验追踪和 SQLite 记录逻辑
    report_generator.py          # Markdown 报告生成逻辑
    utils.py                     # 通用工具函数
  example_data/
    yolo_demo/                   # 模拟 YOLO 数据集
    yolo_results/results.csv     # 模拟 YOLO 训练结果
  reports/                       # 示例 Markdown 报告
  screenshots/                   # 项目截图目录
  docs/                          # 项目说明文档
  data/                          # 本地运行数据目录
```

## 技术栈

- Python
- Streamlit
- Pandas
- Pillow
- SQLite

## Roadmap

- 误检漏检分析 Error Analyzer
- 阈值/NMS 扫描
- hard case 样本管理
- 更多可视化图表
- README 英文版 `README_EN.md`
- GitHub Release 版本整理
