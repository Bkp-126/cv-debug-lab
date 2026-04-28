# cv-debug-lab

面向计算机视觉训练流程的轻量级诊断工具箱。

A lightweight debugging toolkit for computer vision training workflows.

## 项目简介

cv-debug-lab 是一个面向个人算法工程师的本地化 CV 训练诊断工具箱，用于辅助检查 YOLO 数据集质量、记录实验结果、生成训练诊断报告。

当前版本重点解决训练前的数据集体检和训练后的实验记录问题：快速发现图片和标签不匹配、空标签、bbox 越界、bbox 宽高非法、类别分布异常等常见问题，同时记录训练指标并生成可复盘的 Markdown 报告。

## 为什么做这个项目

在真实 CV 项目中，模型效果不好往往不只是模型结构或训练参数的问题，也可能来自数据和实验管理环节：

- 数据集结构问题
- 标注质量问题
- train/val 划分问题
- 空标签和异常框问题
- 实验结果无法复盘

cv-debug-lab 的目标是把这些容易被忽略的工程问题显式化，让训练前检查、训练后复盘和报告输出变得更轻量、更稳定。

## 当前功能

目前 V0.1 支持：

- YOLO 数据集体检
- 图片和标签匹配检查
- 空标签检查
- bbox 越界检查
- bbox 宽高非法检查
- 类别分布统计
- 每张图片目标框数量统计
- 实验追踪
- YOLO results.csv 指标解析
- SQLite 本地实验记录
- 实验对比表
- 中文实验报告导出
- Markdown 报告生成

## 技术栈

- Python
- Streamlit
- Pandas
- Pillow
- SQLite，后续实验记录模块使用

## 快速开始

Windows PowerShell 示例：

```powershell
conda create -n cv-debug-lab python=3.11 -y
conda activate cv-debug-lab
pip install -r requirements.txt
streamlit run app.py
```

启动后，在页面中点击 `运行数据集体检`，即可扫描默认示例数据集并生成 Markdown 报告。

## 项目结构

```text
cv-debug-lab/
  app.py                         # Streamlit 应用入口
  README.md                      # 项目说明文档
  requirements.txt               # Python 依赖列表
  .gitignore                     # 本地文件和模型产物排除规则
  LICENSE                        # 开源许可证
  src/
    __init__.py
    dataset_auditor.py           # YOLO 数据集体检逻辑
    experiment_tracker.py        # 实验追踪和 SQLite 记录逻辑
    report_generator.py          # Markdown 报告生成逻辑
    utils.py                     # 通用工具函数
  example_data/
    yolo_demo/                   # 模拟 YOLO 数据集
      images/
        train/
        val/
      labels/
        train/
        val/
    yolo_results/
      results.csv                # 模拟 YOLO 训练结果
  reports/                       # 生成的 Markdown 报告
  data/                          # 后续 SQLite 数据文件目录
  screenshots/                   # 后续 GitHub 展示截图目录
```

## 示例数据说明

`example_data/yolo_demo` 是一份模拟 YOLO 数据集，仅用于开源演示。图片由简单几何图形生成，标签文件刻意覆盖正常标签、空标签、bbox 越界、bbox 宽高非法、图片缺少标签、标签缺少图片等情况。

该示例数据不包含任何公司或真实业务数据。

## 脱敏说明

本项目是通用 CV 工具项目，不包含公司项目代码、真实业务数据、模型权重、现场日志或内部接口文档。

## Roadmap

- 实验结果追踪 Experiment Tracker
- 误检漏检分析 Error Analyzer
- 阈值/NMS 扫描
- 自动生成训练复盘报告
- GitHub 展示截图补充
