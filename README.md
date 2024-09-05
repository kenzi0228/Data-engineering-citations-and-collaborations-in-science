# Data Engineering: Citations and Collaborations in Science

## Overview
This project, conducted as part of my MIAGE curriculum at the University of Nanterre, explores the applications of graph theory and operational research, particularly for analyzing scientific citation and collaboration networks. By examining these networks, we aim to:
- Identify the most influential researchers
- Detect collaboration communities
- Understand the underlying dynamics of academic interactions

## Objectives
- **Graph Creation**: Generate graphs from citation and collaboration data to identify the most influential nodes.
- **Community Detection**: Use algorithms to detect communities within networks and interpret complex relationships between researchers.
- **Centrality Metrics Calculation**: Evaluate the importance of nodes by calculating various centrality metrics (degree, closeness, betweenness).
- **Network Visualization**: Utilize visualization tools to dynamically represent networks and facilitate data exploration.

## Data
The data for citation and collaboration was retrieved from the AMiner Citation Network. The dataset, in JSON format, contains 5,354,309 records with 48,227,950 citation relations, dated May 14, 2021.

## Project Structure

### Data Collection and Preparation
1. Download and split the large JSON file into manageable segments.
2. Preprocess the data to correct format errors and clean unnecessary columns.
3. Filter data by year, field of study, or other criteria.

### Graph Creation
1. Generate citation and collaboration graphs using the filtered data.
2. Save the graphs in GEXF format for detailed visualization in Gephi.

### Graph Analysis
Apply various algorithms to analyze the graphs, including:
- Community detection (Louvain algorithm)
- Centrality metrics (degree, closeness, betweenness)
- PageRank calculation
- Shortest path analysis (Dijkstra's algorithm)
- Clustering coefficient and graph diameter calculation

### Visualization
- Use Gephi to create dynamic and interactive visualizations of the networks.
- Employ layouts like Force Atlas 2, Yifan Hu, and Fruchterman Reingold for better clarity and understanding.

## Installation

### Clone the Repository

First, clone the repository to your local machine using the following commands:

```bash
git clone https://github.com/kenzi0228/Data-engineering-citations-and-collaborations-in-science.git
cd Data-engineering-citations-and-collaborations-in-science

### Install Dependencies
The project relies on several Python libraries. Install them using:

```bash
pip install -r requirements.txt

### Data Preparation
Download the dataset from **AMiner** and place it in the `Dataset` directory.
Use the provided scripts to preprocess and filter the data.

## Usage

### Data Preprocessing
- **CorrectionFormatJSON.py**: Splits and corrects the JSON format.
- **PretraiterNumberInt.py**: Converts year fields to integers.
- **NettoyerColonnes.py**: Cleans unnecessary columns.

### Graph Analysis
- **DessinerGraphe.py**: Creates citation and collaboration graphs.
- **AnalyseGraphe.py**: Performs various graph analyses.
- **NettoyerGraphe.py**: Ensures graph integrity before analysis.

### Visualization
- Use **Gephi** to visualize the generated GEXF files.

## Results
The analysis of the citation and collaboration networks led to several key findings:

- **Influential Researchers and Publications**: Identified through centrality metrics and PageRank scores.
- **Collaboration Communities**: Detected with the Louvain algorithm, revealing tightly-knit collaboration groups.
- **Network Dynamics**: Visualizations provided insights into trends and key figures across various research fields.

## Conclusion
This project highlights the power of **graph theory** and **open data** in understanding the dynamics of academic and scientific networks. The methodologies and tools used here offer a solid foundation for future research, helping researchers and decision-makers gain deeper insights into collaboration and citation networks.

## Future Work
Planned enhancements for the project include:

- Developing an **integrated graphical interface** to simplify usage for non-technical users.
- Modularizing the Python scripts into **classes** to improve code maintainability and flexibility.
- Expanding the project to allow users to **customize filters and criteria** for network generation and analysis.


References
Newman, M. (2010). Networks: An Introduction. Oxford University Press.
Barabási, A.-L. (2016). Network Science. Cambridge University Press.
NetworkX Documentation
Gephi Documentation
AMiner Dataset
