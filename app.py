"""Streamlit entry point for cv-debug-lab."""

import streamlit as st


def main() -> None:
    """Render the cv-debug-lab V0.1 home page."""
    st.set_page_config(
        page_title="cv-debug-lab",
        layout="wide",
    )

    st.title("cv-debug-lab")
    st.write(
        "A lightweight debugging toolkit for computer vision training workflows."
    )

    st.divider()

    st.header("Modules")
    columns = st.columns(3)
    modules = [
        (
            "Dataset Auditor",
            "Inspect YOLO-style datasets and surface common annotation issues.",
        ),
        (
            "Experiment Tracker",
            "Record training runs, metrics, notes, and lightweight experiment metadata.",
        ),
        (
            "Report Generator",
            "Generate readable Markdown summaries for datasets and training runs.",
        ),
    ]

    for column, (name, description) in zip(columns, modules):
        with column:
            st.subheader(name)
            st.write(description)

    st.header("V0.1 Roadmap")
    st.markdown(
        """
- Create a minimal Streamlit home page.
- Add YOLO dataset structure checks.
- Parse sample training metrics from `results.csv`.
- Store experiment notes in SQLite.
- Export Markdown reports for local review.
"""
    )


if __name__ == "__main__":
    main()
