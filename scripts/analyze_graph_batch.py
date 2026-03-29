import os
import networkx as nx
import community as community_louvain
from networkx.algorithms import community as nx_community
from networkx.algorithms.centrality import degree_centrality, closeness_centrality, betweenness_centrality
from networkx.algorithms.link_analysis import pagerank_alg
from networkx.algorithms.flow import maximum_flow
from networkx.algorithms.matching import max_weight_matching
from networkx.algorithms.shortest_paths.dense import floyd_warshall
from networkx.algorithms.tree import minimum_spanning_tree

def list_gexf_files(directory):
    """ List all GEXF files in a directory. """
    return [file for file in os.listdir(directory) if file.endswith('.gexf')]

def load_graph(file_path):
    """ Load a GEXF file into a NetworkX graph. """
    return nx.read_gexf(file_path)

def graph_details(graph):
    graph_undirected = graph.to_undirected()
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    degree_centrality = nx.degree_centrality(graph)
    betweenness_centrality = nx.betweenness_centrality(graph)
    closeness_centrality = nx.closeness_centrality(graph)
    clustering_coefficient = nx.average_clustering(graph_undirected)
    largest_component = max(nx.connected_components(graph_undirected), key=len)
    subgraph_largest_component = graph_undirected.subgraph(largest_component)
    diameter = nx.diameter(subgraph_largest_component)
    density = nx.density(graph)

    return {
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "degree_centrality": list(degree_centrality.items())[:5],
        "betweenness_centrality": list(betweenness_centrality.items())[:5],
        "closeness_centrality": list(closeness_centrality.items())[:5],
        "clustering_coefficient": clustering_coefficient,
        "diameter": diameter,
        "density": density
    }

def detect_communities(graph):
    partition = community_louvain.best_partition(graph)
    num_communities = len(set(partition.values()))
    return partition, num_communities

def calculate_centralities(graph):
    degree = degree_centrality(graph)
    closeness = closeness_centrality(graph)
    betweenness = betweenness_centrality(graph)
    return degree, closeness, betweenness

def calculate_pagerank(graph):
    return pagerank_alg.pagerank(graph)

def clustering_coefficient(graph):
    return nx.average_clustering(graph)

def graph_diameter(graph):
    largest_component = max(nx.connected_components(graph), key=len)
    subgraph = graph.subgraph(largest_component)
    return nx.diameter(subgraph)

def max_matching(graph):
    return max_weight_matching(graph, maxcardinality=True)

def minimum_spanning_tree_network(graph):
    return minimum_spanning_tree(graph)

def main():
    source_directory = r"C:\Users\Kenzi\Documents\MIASHS\L3 MIAGE\Nanterre\Semestre 6\GRAPHES ET OPEN DATA\projet\Dataset\Graphe"
    files = list_gexf_files(source_directory)

    while True:
        print("\nSélectionnez un fichier GEXF à analyser (ou entrez 0 pour quitter) :")
        for i, file in enumerate(files, start=1):
            print(f"{i}. {file}")
        file_choice = input("Entrez le numéro du fichier : ").strip()

        if file_choice == '0':
            print("Sortie du programme.")
            break

        try:
            file_choice = int(file_choice)
            if file_choice < 1 or file_choice > len(files):
                print("Choix invalide. Veuillez sélectionner un numéro valide.")
                continue
        except ValueError:
            print("Choix invalide. Veuillez entrer un chiffre.")
            continue

        file_path = os.path.join(source_directory, files[file_choice - 1])
        graph = load_graph(file_path)

        print(f"Analyse automatique du fichier : {file_path}")

        # 1. Détection de communautés (Louvain)
        #partition, num_communities = detect_communities(graph)
        #print(f"Nombre de communautés détectées (Louvain) : {num_communities}")
        #print(f"Exemple de partitions de communauté : {list(partition.items())[:5]}")

        # 2. Calcul des centralités (degré, proximité, intermédiarité)
        degree, closeness, betweenness = calculate_centralities(graph)
        print("Top 5 des centralités de degré :")
        print(sorted(degree.items(), key=lambda x: x[1], reverse=True)[:5])
        print("Top 5 des centralités de proximité :")
        print(sorted(closeness.items(), key=lambda x: x[1], reverse=True)[:5])
        print("Top 5 des centralités d'intermédiarité :")
        print(sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5])

        # 3. Calcul du PageRank
        pagerank = calculate_pagerank(graph)
        print("Top 5 des scores de PageRank :")
        print(sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5])

        # 5. Coefficient de clustering
        coefficient = clustering_coefficient(graph)
        print(f"Coefficient de clustering moyen : {coefficient}")

        # 6. Diamètre du graphe
        diameter = graph_diameter(graph)
        print(f"Diamètre du graphe : {diameter}")

        # 8. Détails sur le graphe
        details = graph_details(graph)
        print("Détails du graphe :")
        for key, value in details.items():
            print(f"{key}: {value}")

        # 9. Matching maximum
        matching = max_matching(graph)
        print(f"Matching maximum : {matching}")

        # 10. Arbre couvrant minimum
        mst = minimum_spanning_tree_network(graph)
        print(f"Arbre couvrant minimum : {mst.edges(data=True)}")

if __name__ == "__main__":
    main()
