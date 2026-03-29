import pandas as pd
import json
import os

def extract_unique_fos(input_json_path, output_json_path):
    # Charger les données JSON dans un DataFrame
    data = pd.read_json(input_json_path)
    
    # Vérifier si 'fos' est dans le DataFrame et procéder si c'est le cas
    if 'fos' in data.columns:
        # Utiliser une compréhension de set pour extraire tous les éléments uniques des listes de 'fos'
        unique_fos = set()
        for fos_list in data['fos'].dropna():
            unique_fos.update(fos_list)
        
        # Convertir le set en liste pour le sauvegarder en JSON
        unique_fos_list = list(unique_fos)
        
        # Sauvegarder la liste des champs d'étude uniques dans un fichier JSON
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(unique_fos_list, f, indent=4)
        
        print(f"Les champs d'étude uniques ont été sauvegardés dans : {output_json_path}")
    else:
        print("La colonne 'fos' n'est pas présente dans les données fournies.")

if __name__ == "__main__":
    # Obtenir le chemin du répertoire du script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Spécifiez les chemins relatifs vers les fichiers d'entrée et de sortie
    input_json_path = os.path.join(current_dir, '..', 'Dataset', 'Split_filtré', 'Split_9_Filtered_by_2020.json')
    output_json_path = os.path.join(current_dir, '..', 'Dataset', 'UniqueFOS.json')

    # Appeler la fonction pour extraire et sauvegarder les FOS uniques
    extract_unique_fos(input_json_path, output_json_path)

