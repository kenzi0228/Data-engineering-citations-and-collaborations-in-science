import json
import os

def search_term_in_files(directory, term):
    results = {}
    files = [f for f in os.listdir(directory) if f.endswith('.json')]
    
    for filename in files:
        file_path = os.path.join(directory, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
            
                if isinstance(data, dict):  
                    data = [data]
                for record in data:
                    for key, value in record.items():
                        if isinstance(value, str) and term.lower() in value.lower():
                            if filename not in results:
                                results[filename] = []
                            results[filename].append((record['_id'], key, value))
                        elif isinstance(value, list):  # Si le champ est une liste, cherchez dans chaque élément
                            for item in value:
                                if isinstance(item, str) and term.lower() in item.lower():
                                    if filename not in results:
                                        results[filename] = []
                                    results[filename].append((record['_id'], key, item))
            except json.JSONDecodeError:
                print(f"Error decoding JSON from file {filename}")
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
    
    return results

# Obtenir le chemin du répertoire du script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Utilisation
directory = os.path.join(current_dir, '..', 'Dataset', 'Split_nettoyé')
term = 'Delbot'
results = search_term_in_files(directory, term)

# Afficher les résultats
for filename, hits in results.items():
    print(f"Found in {filename}:")
    for hit in hits:
        print(f"  ID: {hit[0]}, Field: {hit[1]}, Value: {hit[2]}")

