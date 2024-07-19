import os
import json

def merge_json_files(source_directory, output_directory):
    merged_data = []
    # Extraire le nom du dossier pour le fichier de sortie
    folder_name = os.path.basename(source_directory)
    output_file_name = f"{folder_name}_merged.json"
    output_file_path = os.path.join(output_directory, output_file_name)

    for filename in os.listdir(source_directory):
        if filename.endswith(".json"):
            file_path = os.path.join(source_directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                merged_data.extend(data)

    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(merged_data, output_file, indent=4)

    print(f"Tous les fichiers JSON ont été fusionnés dans : {output_file_path}")

if __name__ == "__main__":
    # Obtenir le chemin du répertoire du script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Chemin relatif du dossier contenant les fichiers JSON à fusionner
    source_directory = os.path.join(current_dir, '..', 'Dataset', 'Split_filtré', 'Filtered_by_5_language')
    # Chemin relatif du dossier de sortie
    output_directory = os.path.join(current_dir, '..', 'Dataset', 'Split_fusionné')

    # Assurer que le répertoire de sortie existe
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Appel de la fonction pour fusionner les fichiers
    merge_json_files(source_directory, output_directory)


