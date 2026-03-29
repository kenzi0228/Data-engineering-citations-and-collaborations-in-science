import json
import os

def filter_json(input_path, output_path):
    keep_keys = {'_id', 'title', 'authors', 'year', 'fos', 'references'}
    results = []

    with open(input_path, 'r', encoding='utf-8') as input_file:
        # Charger le fichier JSON complet
        data = json.load(input_file)

        # Itérer à travers chaque enregistrement dans le tableau JSON
        for record in data:
            # Créer un dictionnaire filtré avec seulement les clés souhaitées
            filtered_record = {k: record[k] for k in keep_keys if k in record}
            results.append(filtered_record)

    with open(output_path, 'w', encoding='utf-8') as output_file:
        # Écrire le résultat dans un nouveau fichier JSON
        json.dump(results, output_file, indent=4)

# Obtenir le chemin du répertoire du script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Chemin du dossier contenant les fichiers JSON d'entrée
input_folder_path = os.path.join(current_dir, '..', 'Dataset', 'Split_prétraité')
# Chemin du dossier destiné à recevoir les fichiers JSON filtrés
output_folder_path = os.path.join(current_dir, '..', 'Dataset', 'Split_nettoyé')

# Vérifier que le dossier d'entrée existe
if not os.path.exists(input_folder_path):
    raise FileNotFoundError(f"Le dossier d'entrée spécifié n'existe pas : {input_folder_path}")

# Création du répertoire de sortie s'il n'existe pas
os.makedirs(output_folder_path, exist_ok=True)

# Parcourir tous les fichiers dans le dossier d'entrée
for file in os.listdir(input_folder_path):
    if file.startswith("Split_") and file.endswith("prétraité.json"):
        # Construire le chemin complet vers le fichier d'entrée
        input_json_path = os.path.join(input_folder_path, file)
        # Construire le chemin complet vers le fichier de sortie
        output_json_path = os.path.join(output_folder_path, file.replace("prétraité", "nettoyé"))

        # Appliquer le filtrage sur le fichier
        filter_json(input_json_path, output_json_path)
        print(f"Le fichier {file} a été filtré et sauvegardé dans {output_json_path}.")

