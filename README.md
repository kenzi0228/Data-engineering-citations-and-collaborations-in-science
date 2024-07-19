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
```bash
git clone https://github.com/kenzi0228/Data-engineering-citations-and-collaborations-in-science.git
cd Data-engineering-citations-and-collaborations-in-science
Install Dependencies
The project relies on several Python libraries. Install them using pip:
pip install -r requirements.txt

Data Preparation
Download the dataset from AMiner and place it in the Dataset directory. Use the provided scripts to preprocess and filter the data as described in the project structure.

Usage
The project includes several scripts for different stages of the analysis:

Data Preprocessing

CorrectionFormatJSON.py: Split and correct JSON format.
PretraiterNumberInt.py: Convert year fields to integers.
NettoyerColonnes.py: Clean unnecessary columns.
Graph Analysis

DessinerGraphe.py: Create citation and collaboration graphs.
AnalyseGraphe.py: Perform various analyses on the graphs.
NettoyerGraphe.py: Ensure graph integrity before analysis.
Visualization

Use Gephi to visualize the generated GEXF files.
Results
The analysis revealed significant insights into academic networks, including:

Influential Researchers and Publications: Identified through centrality metrics and PageRank scores.
Collaboration Communities: Detected using the Louvain algorithm, showing closely collaborating groups.
Network Dynamics: Visualizations highlighted trends and key players in various research fields.
Conclusion
This project demonstrated the importance and utility of graph theory and open data in understanding academic and scientific dynamics. The methodologies developed can serve as a foundation for future analyses, helping researchers and decision-makers gain deeper insights into academic networks.

Future Work
Future enhancements include developing an integrated graphical interface and modularizing the Python scripts into classes. This would make the project more accessible to non-technical users, allowing them to easily apply filters and criteria for creating and analyzing custom networks.

References
Newman, M. (2010). Networks: An Introduction. Oxford University Press.
Barabási, A.-L. (2016). Network Science. Cambridge University Press.
NetworkX Documentation
Gephi Documentation
AMiner Dataset
