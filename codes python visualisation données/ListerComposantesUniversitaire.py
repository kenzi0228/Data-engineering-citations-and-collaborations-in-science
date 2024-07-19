import pandas as pd
import json
import os

def extract_unique_orgs(source_directory, output_json_path):
    unique_orgs = set()

    for filename in os.listdir(source_directory):
        file_path = os.path.join(source_directory, filename)
        try:
            # Si vos fichiers sont de grands tableaux JSON, n'utilisez pas lines=True
            data = pd.read_json(file_path)
            
            if 'authors' in data.columns:
                # Itérer à travers chaque ligne de données
                for idx, row in data.iterrows():
                    authors = row['authors']
                    if authors is not None:
                        for author in authors:
                            # Extraire 'org' si présent
                            if 'org' in author:
                                unique_orgs.add(author['org'])
                            # Extraire chaque 'org' dans 'orgs' si présent
                            if 'orgs' in author:
                                unique_orgs.update(set(author['orgs']))
        except ValueError as e:
            print(f"Erreur lors du traitement du fichier {filename}: {e}")
        except Exception as e:
            print(f"Erreur non spécifiée pour le fichier {filename}: {e}")

    # Sauvegarder les organisations uniques dans un fichier JSON
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(list(unique_orgs), f, indent=4)

    print(f"Les organisations uniques ont été sauvegardées dans : {output_json_path}")

if __name__ == "__main__":
    # Obtenir le chemin du répertoire du script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Spécifiez les chemins relatifs vers les fichiers d'entrée et de sortie
    source_directory = os.path.join(current_dir, '..', 'Dataset', 'Split_nettoyé')
    output_json_path = os.path.join(current_dir, '..', 'Dataset', 'UniqueOrgs.json')

    # Appeler la fonction pour extraire et sauvegarder les organisations uniques
    extract_unique_orgs(source_directory, output_json_path)

