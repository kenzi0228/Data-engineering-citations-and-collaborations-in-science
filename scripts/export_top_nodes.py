import os
import json
from tqdm import tqdm

def list_json_files(directory):
    """List all JSON files in a directory."""
    return [file for file in os.listdir(directory) if file.endswith('.json')]

def extract_top_nodes(file_path, top_n=1000, network_type='1'):
    """Extract the top_n nodes with the highest number of citations or collaborations."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except json.JSONDecodeError:
        print(f"Failed to decode JSON from {file_path}")
        return []

    # Initialize dictionaries to count citations or collaborations
    in_degree_counts = {}
    out_degree_counts = {}
    node_data = {}

    for record in data:
        node_id = record.get('_id')
        if node_id in (None, 'unknown'):
            continue

        # Initialize node data
        if node_id not in node_data:
            node_data[node_id] = record.copy()
            node_data[node_id]['degré entrant'] = 0
            node_data[node_id]['degré sortant'] = 0

        if network_type == '1':
            if 'references' in record and isinstance(record['references'], list):
                for ref in record['references']:
                    if ref and ref != 'unknown':
                        in_degree_counts[ref] = in_degree_counts.get(ref, 0) + 1
        elif network_type == '2':
            if 'authors' in record and isinstance(record['authors'], list):
                authors = [author.get('_id') for author in record['authors'] if author.get('_id') and author.get('_id') != 'unknown']
                for author in authors:
                    out_degree_counts[author] = out_degree_counts.get(author, 0) + len(authors) - 1

    # Update node data with degree counts
    for node_id, in_degree in in_degree_counts.items():
        if node_id in node_data:
            node_data[node_id]['degré entrant'] = in_degree
    for node_id, out_degree in out_degree_counts.items():
        if node_id in node_data:
            node_data[node_id]['degré sortant'] = out_degree

    # Sort nodes by counts and select top_n
    if network_type == '1':
        sorted_nodes = sorted(node_data.values(), key=lambda x: x['degré entrant'], reverse=True)[:top_n]
    else:
        sorted_nodes = sorted(node_data.values(), key=lambda x: x['degré sortant'], reverse=True)[:top_n]

    return sorted_nodes

def save_json(data, output_path):
    """Save data to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def process_directory(source_directory, output_directory, top_n=1000, network_type='1'):
    """Process all JSON files in a source directory for the specified network type."""
    files = list_json_files(source_directory)
    all_top_nodes = []

    for file in tqdm(files, desc=f"Processing {network_type} files"):
        file_path = os.path.join(source_directory, file)
        top_nodes_data = extract_top_nodes(file_path, top_n, network_type)
        all_top_nodes.extend(top_nodes_data)
        
        # Save the top nodes data for the individual file
        base_filename = os.path.splitext(os.path.basename(file_path))[0]
        json_filename = os.path.join(output_directory, f"{base_filename}_top_{top_n}_{network_type}.json")
        save_json(top_nodes_data, json_filename)

    # Save the merged top nodes data
    merged_json_filename = os.path.join(output_directory, f"merged_top_{top_n}_{network_type}.json")
    save_json(all_top_nodes, merged_json_filename)
    print(f"Merged top nodes for {network_type} saved to {merged_json_filename}")

    # Remove individual JSON files
    for file in list_json_files(output_directory):
        if file != os.path.basename(merged_json_filename):
            os.remove(os.path.join(output_directory, file))
    print("Individual JSON files have been deleted.")

# Configuration utilisateur
current_dir = os.path.dirname(os.path.abspath(__file__))

source_directory = os.path.join(current_dir, '..', 'Dataset', 'Split_fusionné', 'Année')
output_directory = os.path.join(current_dir, '..', 'Dataset', 'Split_fusionné', 'collaboration')
network_type = input("Tapez '1' pour un réseau de citations, '2' pour un réseau de collaboration : ").strip().lower()
top_n = 1000

# Ensure the output directory exists
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Process files
process_directory(source_directory, output_directory, top_n, network_type)











