# cv-debug-lab

cv-debug-lab is a lightweight debugging toolkit for computer vision training workflows.

The project is designed for individual algorithm engineers who need a simple local tool for YOLO dataset checks, experiment record management, and Markdown report generation.

## Core Feature Plan

- Dataset Auditor: inspect YOLO-style dataset structure, labels, class distribution, and common annotation issues.
- Experiment Tracker: record training runs, metrics, notes, and lightweight experiment metadata.
- Report Generator: generate readable Markdown reports for dataset audits and training summaries.

## Tech Stack

- Python
- Streamlit
- SQLite
- Pandas

## Quick Start

Create a virtual environment, install dependencies, and start the Streamlit app:

```bash
python -m venv .venv
pip install -r requirements.txt
streamlit run app.py
```

## Directory Structure

```text
cv-debug-lab/
  app.py
  README.md
  requirements.txt
  .gitignore
  LICENSE
  src/
    __init__.py
    dataset_auditor.py
    experiment_tracker.py
    report_generator.py
    utils.py
  example_data/
    yolo_demo/
      images/
        train/
        val/
      labels/
        train/
        val/
    yolo_results/
      results.csv
  reports/
  data/
  screenshots/
```

## Data Desensitization

This project uses simulated data only. It does not contain any company data, private datasets, real business records, or sensitive production information.

## Status

V0.1 is an initialization milestone. The current code provides a runnable project skeleton and placeholder modules for future implementation.
