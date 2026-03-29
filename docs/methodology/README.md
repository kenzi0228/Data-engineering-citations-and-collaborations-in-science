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

This project uses the **AMiner DBLP Citation Network Dataset**.

Source:
- AMiner Open Data: `https://www.aminer.org/open/article?id=655db2202ab17a072284bc0c`

Dataset version used in this project:
- **DBLP-Citation-network V13**
- **Release date: 2021-05-14**

The dataset contains large-scale academic publication metadata and citation relationships extracted from sources such as **DBLP, ACM, MAG (Microsoft Academic Graph), and others**.

Typical fields used in this project include:
- paper identifiers (`_id`)
- titles
- authors
- year
- fields of study (`fos`)
- references / citations

Because the original dataset is large and not suitable for direct versioning in GitHub, raw files are not stored in this repository. Instead, this repository provides preprocessing, filtering, graph construction, analysis, and export utilities built around that dataset.
---

## Methodology

The project now follows a clearer engineering pipeline:

### 1. Dataset preprocessing
Raw dataset files are repaired and standardized before analysis:
- malformed JSON fixes
- `NumberInt(...)` normalization
- field selection / schema simplification

### 2. Filtering and extraction
Relevant subsets can be produced using:
- exact year filters
- year range filters
- before / after year filters
- field-of-study filtering
- metadata search utilities

### 3. Graph construction
Two graph types can be built from the dataset:
- **citation graph**: directed graph linking referenced papers to citing papers
- **collaboration graph**: undirected weighted graph linking co-authors

### 4. Graph analysis
The analysis pipeline includes:
- graph summary metrics
- centrality measures
- PageRank
- community detection
- shortest path inspection
- top node export

### 5. Graph repair and export
The repository also includes utilities to:
- repair malformed GEXF files
- export metrics as JSON
- export graph files for tools such as Gephi
- optionally generate graph images

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
│   ├── preprocess_dataset.py
│   ├── filter_dataset.py
│   ├── merge_files.py
│   ├── build_graph.py
│   ├── analyze_graph.py
│   ├── export_top_nodes.py
│   ├── search_dataset.py
│   ├── repair_gexf.py
│   └── split_dataset_2gb.py
├── src/
│   └── citation_graphs/
│       ├── __init__.py
│       ├── io.py
│       ├── preprocessing.py
│       ├── filtering.py
│       ├── graph_builder.py
│       ├── graph_analysis.py
│       ├── graph_cleaning.py
│       ├── export.py
│       ├── search.py
│       └── utils.py
├── tests/
│   ├── test_preprocessing.py
│   ├── test_graph_builder.py
│   └── test_graph_analysis.py
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements.txt
```

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

## Tech Stack

- **Python**
- **NetworkX**
- **Pandas**
- **NumPy**
- **Matplotlib**
- **python-louvain**
- **lxml**
- **pytest**
- **Jupyter Notebook**
- **Gephi** (for graph exploration and visualization)

## Key Skills Demonstrated

This repository showcases practical skills in:

- preprocessing large semi-structured academic datasets
- graph-based data modeling
- citation and collaboration network construction
- CLI-oriented data pipeline design
- network analysis and metric extraction
- modular Python project structuring
- export and interoperability with graph visualization tooling
- basic automated testing for core graph and preprocessing logic

## Current Limitations

The repository has been significantly cleaned and modularized, but some limitations still remain:

- the raw AMiner dataset is not bundled in the repository because of its size
- large-scale graph computations can become expensive depending on the selected subset
- visualization with spring layouts is not suitable for very large graphs
- the test suite currently focuses on core units rather than full end-to-end pipelines
- configuration is still CLI-driven and not yet centralized in a dedicated config system

## Roadmap

Planned next improvements include:

- adding end-to-end pipeline tests
- introducing centralized configuration management
- adding logging across all scripts
- providing a small reproducible sample dataset
- improving performance for larger graph subsets
- adding richer documentation for graph semantics and output interpretation

## Author

Kenzi Lali

GitHub: kenzi0228

