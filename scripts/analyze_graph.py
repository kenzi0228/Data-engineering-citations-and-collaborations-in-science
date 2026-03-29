import os
import networkx as nx
import community as community_louvain
import json
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

def save_json(data, file_path):
    """ Save data to a JSON file. """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

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

def display_centralities(graph, centrality_data, centrality_name):
    top_5 = sorted(centrality_data.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"Top 5 des centralités de {centrality_name} :")
    for node_id, value in top_5:
        node_label = graph.nodes[node_id].get('name') or graph.nodes[node_id].get('title', 'N/A')
        print(f"{node_id} ({node_label}): {value}")


def calculate_pagerank(graph):
    return pagerank_alg.pagerank(graph)

def shortest_path(graph, source, target):
    try:
        return nx.shortest_path(graph, source=source, target=target)
    except nx.NetworkXNoPath:
        return None

def clustering_coefficient(graph):
    return nx.average_clustering(graph)

def graph_diameter(graph):
    graph_undirected = graph.to_undirected()
    largest_component = max(nx.connected_components(graph_undirected), key=len)
    subgraph = graph_undirected.subgraph(largest_component)
    return nx.diameter(subgraph)

def maximum_flow_network(graph, source, target):
    return maximum_flow(graph, source, target)

def max_matching(graph):
    return max_weight_matching(graph, maxcardinality=True)

def minimum_spanning_tree_network(graph):
    return minimum_spanning_tree(graph)

def floyd_warshall_paths(graph):
    return floyd_warshall(graph)

def list_node_details(graph, node_id):
    """ List the details of a node with the specified ID. """
    if node_id in graph.nodes:
        return dict(graph.nodes[node_id])
    else:
        return None

def main():
    # Obtenir le chemin du répertoire du script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    source_directory = os.path.join(current_dir, '..', 'Dataset', 'Graphe')
    output_directory = os.path.join(current_dir, 'output')
    os.makedirs(output_directory, exist_ok=True)
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
        base_filename = os.path.splitext(files[file_choice - 1])[0]

        while True:
            print("\nSélectionnez l'analyse à effectuer (ou entrez 0 pour revenir au choix du fichier, 99 pour quitter) :")
            print("1. Détection de communautés (Louvain)")
            print("2. Calcul des centralités (degré, proximité, intermédiarité)")
            print("3. Calcul du PageRank")
            print("4. Analyse du chemin le plus court entre deux chercheurs (Dijkstra)")
            print("5. Coefficient de clustering")
            print("6. Diamètre du graphe")
            print("7. Flux maximum entre deux nœuds")
            print("8. Détails sur le graphe")
            print("9. Matching maximum")
            print("10. Arbre couvrant minimum")
            print("11. Plus courts chemins entre toutes les paires de nœuds (Floyd-Warshall)")
            print("12. Détails d'un nœud spécifique")

            choice = input("Entrez le numéro de l'analyse à effectuer : ").strip()

            if choice == '0':
                break
            elif choice == '99':
                print("Sortie du programme.")
                return

            if choice == '1':
                partition, num_communities = detect_communities(graph)
                print(f"Nombre de communautés détectées (Louvain) : {num_communities}")
                print(f"Exemple de partitions de communauté : {list(partition.items())[:5]}")
            elif choice == '2':
                degree, closeness, betweenness = calculate_centralities(graph)
                display_centralities(graph, degree, "degré")
                display_centralities(graph, closeness, "proximité")
                display_centralities(graph, betweenness, "intermédiarité")
        
            elif choice == '3':
                pagerank = calculate_pagerank(graph)
                print("Top 5 des scores de PageRank :")
                print(sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5])
            elif choice == '4':
                source = input("Entrez l'ID du chercheur source : ")
                target = input("Entrez l'ID du chercheur cible : ")
                path = shortest_path(graph, source, target)
                if path:
                    print(f"Le chemin le plus court entre {source} et {target} est : {path}")
                else:
                    print(f"Aucun chemin trouvé entre {source} et {target}")
            elif choice == '5':
                coefficient = clustering_coefficient(graph)
                print(f"Coefficient de clustering moyen : {coefficient}")
            elif choice == '6':
                diameter = graph_diameter(graph)
                print(f"Diamètre du graphe : {diameter}")
            elif choice == '7':
                source = input("Entrez l'ID du nœud source : ")
                target = input("Entrez l'ID du nœud cible : ")
                flow_value, flow_dict = maximum_flow_network(graph, source, target)
                print(f"Flux maximum entre {source} et {target} : {flow_value}")
                print(f"Détails du flux : {flow_dict}")
            elif choice == '8':
                details = graph_details(graph)
                print("Détails du graphe :")
                for key, value in details.items():
                    print(f"{key}: {value}")
            elif choice == '9':
                matching = max_matching(graph)
                matching_result = {"matching": list(matching)}
                print(f"Matching maximum : {matching_result}")
                output_path = os.path.join(output_directory, f"matching_maximum_{base_filename}.json")
                save_json(matching_result, output_path)
                print(f"Résultats du matching maximum sauvegardés dans : {output_path}")
            elif choice == '10':
                mst = minimum_spanning_tree_network(graph)
                mst_result = {"mst_edges": list(mst.edges(data=True))}
                print(f"Arbre couvrant minimum : {mst_result}")
                output_path = os.path.join(output_directory, f"minimum_spanning_tree_{base_filename}.json")
                save_json(mst_result, output_path)
                print(f"Résultats de l'arbre couvrant minimum sauvegardés dans : {output_path}")
            elif choice == '11':
                paths = floyd_warshall_paths(graph)
                paths_result = {"paths": dict(paths)}
                print("Plus courts chemins entre toutes les paires de nœuds :")
                output_path = os.path.join(output_directory, f"floyd_warshall_{base_filename}.json")
                save_json(paths_result, output_path)
                print(f"Résultats des plus courts chemins sauvegardés dans : {output_path}")
            elif choice == '12':
                node_id = input("Entrez l'ID du nœud : ")
                details = list_node_details(graph, node_id)
                if details:
                    print(f"Détails pour le nœud {node_id} :")
                    for key, value in details.items():
                        print(f"{key}: {value}")
                else:
                    print(f"Aucun nœud trouvé avec l'ID {node_id}")
            else:
                print("Choix invalide. Veuillez sélectionner un numéro valide.")

if __name__ == "__main__":
    main()

