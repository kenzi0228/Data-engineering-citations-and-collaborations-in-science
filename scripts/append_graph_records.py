import json
import networkx as nx
from tqdm import tqdm

def load_graph(file_path):
    """ Load an existing GEXF file into a NetworkX graph. """
    return nx.read_gexf(file_path)

def save_graph(graph, file_path):
    """ Save a NetworkX graph to a GEXF file. """
    nx.write_gexf(graph, file_path)
    print(f"Graph saved to {file_path}")

def add_records_to_graph(graph, records, network_type):
    """ Add records to the graph and create necessary edges. """
    for record in tqdm(records, desc="Adding records to graph"):
        node_attributes = {
            'year': str(record.get('year', "")),
            'title': str(record.get('title', "")),
            'fos': ', '.join(record.get('fos', [])) if record.get('fos', None) is not None else "Unknown",
            'references': ', '.join(record.get('references', [])) if record.get('references', None) is not None else "Unknown"
        }

        if network_type == '1':
            # Add node for citation network
            graph.add_node(record['_id'], **node_attributes)
            references = record.get('references', [])
            if isinstance(references, list):
                for ref in references:
                    if ref and ref in graph:
                        graph.add_edge(ref, record['_id'])
        else:
            # Add nodes and edges for collaboration network
            authors = record.get('authors', [])
            if authors:
                for author in authors:
                    if 'name' in author and '_id' in author:
                        author_attributes = {
                            'name': str(author.get('name', "Unknown")),
                            **node_attributes
                        }
                        graph.add_node(author['_id'], **author_attributes)

                for i in range(len(authors)):
                    if '_id' in authors[i]:
                        for j in range(i + 1, len(authors)):
                            if '_id' in authors[j]:
                                graph.add_edge(authors[i]['_id'], authors[j]['_id'])

def main():
    # Paths to the graph file and new records file
    graph_path = r"C:\Users\Kenzi\Documents\MIASHS\L3 MIAGE\Nanterre\Semestre 6\GRAPHES ET OPEN DATA\projet\Dataset\Graphe\Dataset_Collaboration_Top_200_Sommets_merged_citation_network.gexf"
    new_records_path = r"C:\Users\Kenzi\Documents\MIASHS\L3 MIAGE\Nanterre\Semestre 6\GRAPHES ET OPEN DATA\projet\Dataset\Ajout.json"
    updated_graph_path = r"C:\Users\Kenzi\Documents\MIASHS\L3 MIAGE\Nanterre\Semestre 6\GRAPHES ET OPEN DATA\projet\Dataset\Graphe\Dataset_Collaboration_Top_200_Sommets_merged_citation_network.gexf"

    # Load the existing graph
    graph = load_graph(graph_path)

    # Load new records from JSON file
    with open(new_records_path, 'r', encoding='utf-8') as file:
        new_records = json.load(file)

    # Ask the user for the network type
    network_type = input("Type '1' for a citation network, '2' for a collaboration network: ").strip()

    # Add new records to the graph
    add_records_to_graph(graph, new_records, network_type)

    # Save the updated graph
    save_graph(graph, updated_graph_path)

if __name__ == "__main__":
    main()
