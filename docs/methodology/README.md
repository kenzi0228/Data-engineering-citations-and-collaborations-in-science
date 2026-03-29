# Citation and Collaboration Graph Analysis in Science

A data engineering and graph analytics project designed to explore scientific citation networks and collaboration structures from large-scale academic datasets.

This project focuses on transforming raw scientific metadata into usable graph structures, then extracting meaningful insights through network analysis, graph cleaning, filtering, and visualization workflows.

---

## Project Overview

Scientific research generates complex relational data:
- papers cite other papers,
- authors collaborate across institutions,
- disciplines form interconnected communities.

This project builds a processing pipeline to:
1. preprocess raw scientific data,
2. filter and clean relevant entities,
3. construct citation and collaboration graphs,
4. analyze graph properties,
5. export graph outputs for visualization and downstream exploration.

The project was built around graph-based analysis of academic open data and aims to demonstrate practical data engineering, graph modeling, and exploratory network analysis skills.

---

## Objectives

The main goals of the project are:

- transform raw academic datasets into structured graph-ready data,
- build and manipulate citation / collaboration graphs,
- compute graph metrics and identify influential nodes,
- clean and simplify graph structures,
- export results for visualization in tools such as Gephi,
- provide a reusable workflow for large-scale graph exploration.

---

## Dataset

The project relies on academic metadata from the **AMiner** dataset.

Typical fields used in the workflow include:
- paper identifiers,
- titles and keywords,
- authors,
- affiliations or institutions,
- domains / disciplines,
- references / citations.

Because the original dataset can be large, the project includes utilities for:
- formatting and repairing raw JSON,
- splitting large files,
- filtering subsets of interest,
- cleaning malformed or incomplete records.

> Note: raw datasets are not versioned in this repository due to size constraints.

---

## Methodology

The project workflow can be summarized as follows:

### 1. Data preprocessing
Raw files are cleaned, reformatted, merged, and prepared for analysis.

### 2. Filtering
Relevant subsets are extracted based on search terms, domains, institutions, or other criteria.

### 3. Graph construction
Graphs are created from relationships such as:
- citation links between papers,
- collaboration links between researchers or institutions.

### 4. Graph cleaning
Noise reduction and graph simplification are applied to improve interpretability.

### 5. Graph analysis
The project computes or explores metrics such as:
- connected components,
- centrality indicators,
- PageRank,
- communities,
- influential nodes,
- graph diameter and structural properties.

### 6. Visualization / export
Outputs can be exported for network visualization and exploration.

---

## Repository Structure

```text
.
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── sample/
├── docs/
│   ├── academic/
│   └── methodology/
├── notebooks/
├── outputs/
│   ├── figures/
│   ├── graphs/
│   └── metrics/
├── scripts/
├── src/
│   └── citation_graphs/
├── tests/
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements.txt
```

Tech Stack
Python
NetworkX
Pandas
NumPy
Matplotlib
python-louvain
Jupyter Notebook
Gephi (for graph visualization)

## Installation

Clone the repository:
```bash
git clone https://github.com/kenzi0228/Data-engineering-citations-and-collaborations-in-science.git
cd Data-engineering-citations-and-collaborations-in-science
```

Create a virtual environment:
```bash
python -m venv .venv
```

Activate it:

Windows
```bash
.venv\Scripts\activate
```
macOS / Linux
```bash
source .venv/bin/activate
```
Install dependencies:
```bash 
pip install -r requirements.txt
```

## Usage

At this stage, the project mainly provides script-based workflows.

Examples:
```bash
python scripts/fix_json_format.py
python scripts/filter_dataset.py
python scripts/build_graph.py
python scripts/analyze_graph.py
python scripts/export_top_nodes.py
```

As the repository evolves, these scripts will progressively be converted into reusable modules and CLI-friendly commands.

## Outputs

Depending on the executed workflow, the project can generate:

- cleaned datasets,
- filtered subsets,
- graph files,
- graph metrics,
- top node rankings,
- exported files for visualization.

These outputs should typically be stored in:

- outputs/graphs/
- outputs/metrics/
- outputs/figures/

## Key Skills Demonstrated

This repository showcases skills in:

- data preprocessing on large semi-structured files,
- graph-based data modeling,
- exploratory graph analytics,
- script-based data pipeline design,
- network analysis and visualization preparation,
- repository structuring and engineering hygiene.
- Current Limitations

The current version of the project still has several limitations:

- scripts are not yet fully modularized,
- some workflows remain interactive rather than CLI-driven,
- automated tests are still limited,
- dataset configuration is not yet centralized,
- reproducibility can be improved further.

These limitations are being addressed as part of the repository refactor.

## Roadmap

Planned improvements include:

- refactoring scripts into reusable Python modules,
- adding argparse-based command-line interfaces,
- improving configuration management,
- adding tests for preprocessing and graph building logic,
- creating a small sample dataset for reproducible demos,
- improving logging, documentation, and output standardization.
- Recruiter / Interview Angle

This project is intended to highlight practical capabilities relevant to:

- Data Engineering
- Data Science
- BI / Analytics Engineering
- Graph Analytics / Network Analysis

It demonstrates the ability to work on non-trivial relational data, structure a processing workflow, and extract insight from graph-based systems.

## Author

Kenzi Lali

GitHub: kenzi0228

