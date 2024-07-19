import os
import json
import networkx as nx
import matplotlib.pyplot as plt
import networkx.algorithms.community as nx_comm
from tqdm import tqdm

def list_files_and_choose(directory):
    files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
    if not files:
        print("Aucun fichier trouvé dans le dossier spécifié.")
        return None, None
    print("Fichiers trouvés :")
    for index, file in enumerate(files, start=1):
        print(f"{index}. {file}")
    file_index = int(input("Entrez le numéro du fichier à choisir : "))
    if 1 <= file_index <= len(files):
        chosen_file = files[file_index - 1]
        print(f"Fichier choisi : {chosen_file}")
        return os.path.join(directory, chosen_file), chosen_file
    else:
        print("Numéro de fichier non valide.")
        return None, None

def save_top_nodes(network, output_directory2, base_filename, top_n=1000):
    degrees = network.degree()
    top_nodes = sorted(degrees, key=lambda x: x[1], reverse=True)[:top_n]
    top_nodes_data = [{
        "node_id": node,
        "degree": degree,
        **network.nodes[node]
    } for node, degree in top_nodes]
    
    json_filename = os.path.join(output_directory2, f"{base_filename}_{network_title}_{top_n}_top_nodes.json")
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(top_nodes_data, f, indent=4)
    print(f"Top {top_n} nodes saved to {json_filename}")

def build_network(file_path, network_type):
    G = nx.DiGraph() if network_type == '1' else nx.Graph()
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    for record in tqdm(data, desc="Building network", unit="papers"):
        node_attributes = {
            'year': str(record.get('year', "")),
            'title': str(record.get('title', "")),
            'fos': ', '.join(record.get('fos', [])) if record.get('fos', None) is not None else "Unknown",
            'references': ', '.join(record.get('references', [])) if record.get('references', None) is not None else "Unknown"
        }

        if network_type == '1':
            G.add_node(record['_id'], **node_attributes)
            references = record.get('references', [])
            if isinstance(references, list):  # Vérifie que 'references' est une liste
                for ref in references:
                    if ref and ref in G:
                        G.add_edge(ref, record['_id'])
        else:
            authors = record.get('authors', [])
            if authors:  # Vérifie que 'authors' n'est pas None
                for author in authors:
                    if 'name' in author and '_id' in author:
                        author_attributes = {
                            'name': str(author.get('name', "Unknown")),
                            **node_attributes
                        }
                        G.add_node(author['_id'], **author_attributes)

                for i in range(len(authors)):
                    if '_id' in authors[i]:
                        for j in range(i + 1, len(authors)):
                            if '_id' in authors[j]:
                                G.add_edge(authors[i]['_id'], authors[j]['_id'])

    return G

if __name__ == "__main__":
    # Obtenir le chemin du répertoire du script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    network_type = input("Type '1' for a citation network, '2' for a collaboration network: ")

    file_directory = os.path.join(current_dir, '..', 'Dataset', 'Split_fusionné')
    chosen_file_path, chosen_filename = list_files_and_choose(file_directory)

    output_directory2 = os.path.join(current_dir, '..', 'Dataset', 'Dataset_Collaboration_Top_1000_Sommets')

    if chosen_file_path:
        network = build_network(chosen_file_path, network_type)
        network_title = 'Citation' if network_type == '1' else 'Collaboration'
        base_filename = chosen_filename.replace('.json', '')
        print(f"Le réseau {network_title} a {len(network.nodes())} sommets et {len(network.edges())} arrêtes.")
        
        try:
            communities = nx_comm.greedy_modularity_communities(network)
            community_color_map = {node: i for i, comm in enumerate(communities) for node in comm}
        except ValueError as e:
            print("Erreur lors de la détection des communautés :", e)
            community_color_map = {node: 0 for node in network.nodes()}
        
        pos = nx.spring_layout(network, k=0.1, iterations=20)
        plt.figure(figsize=(12, 12))
        nx.draw_networkx_nodes(network, pos, node_size=5, cmap=plt.cm.jet,
                               node_color=[community_color_map[node] for node in network.nodes()], alpha=0.6)
        nx.draw_networkx_edges(network, pos, alpha=0.5)
        plt.axis('off')
        plt.title(f"Réseau de {network_title} avec Détection de communauté - {base_filename}")
        
        output_directory = os.path.join(current_dir, '..', 'Dataset', 'Graphe')
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        jpeg_filename = os.path.join(output_directory, f"{base_filename}_{network_title.lower()}_network.jpeg")
        plt.savefig(jpeg_filename, format='jpeg', dpi=300)
        print(f"Graphe enregistré sous {jpeg_filename}.")
        
        gexf_filename = os.path.join(output_directory, f"{base_filename}_{network_title.lower()}_network.gexf")
        nx.write_gexf(network, gexf_filename)
        print(f"Le Graphe a été exporté pour Gephi comme : {gexf_filename}.")
        
        plt.show()
    else:
        print("Le fichier n'est pas valide.")

