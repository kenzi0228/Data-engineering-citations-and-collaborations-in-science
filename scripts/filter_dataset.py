import pandas as pd
import os
import json

def filter_files(source_directory, output_directory):
    while True:
        print("\nOptions de filtrage des données:")
        print("1 - Filtrer pour une année précise")
        print("2 - Filtrer pour une plage d'années")
        print("3 - Filtrer pour les années antérieures à une année donnée")
        print("4 - Filtrer pour les années postérieures à une année donnée")
        print("5 - Filtrer par Field of Study (FOS)")
        print("7 - Quitter")
        
        choice = input("Entrez votre choix (1-7): ")
        
        if choice == '7':
            print("Annulation de l'opération.")
            break
        
        if choice in ['1', '3', '4']:
            year = int(input("Entrez l'année: "))
        elif choice == '2':
            year_range = input("Entrez la plage d'années (ex: 2017-2020): ")
            start_year, end_year = map(int, year_range.split('-'))
        fos_list = []
        if choice == '5':
            fos_input = input("Entrez les Fields of Study à filtrer, séparés par des virgules (ex: Computer Science, Mathematics): ")
            fos_list = [fos.strip() for fos in fos_input.split(',')]

        for filename in os.listdir(source_directory):
            if filename.endswith(".json"):
                input_path = os.path.join(source_directory, filename)
                data = pd.read_json(input_path)  # Charger le fichier JSON dans un DataFrame
                
                # Conversion des NaN en None pour compatibilité JSON
                data = data.where(pd.notnull(data), None)
                
                subfolder_name = f"Filtered_by_{choice}_{year if choice in ['1', '3', '4'] else '-'.join(map(str, [start_year, end_year])) if choice == '2' else ','.join(fos_list)}"
                full_output_directory = os.path.join(output_directory, subfolder_name)
                os.makedirs(full_output_directory, exist_ok=True)

                output_filename = f"{filename.replace('.json', '')}_Filtered.json"
                output_path = os.path.join(full_output_directory, output_filename)

                if choice in ['1', '3', '4']:
                    data_filtered = data[data["year"] == year if choice == '1' else (data["year"] < year if choice == '3' else data["year"] > year)]
                elif choice == '2':
                    data_filtered = data[(data["year"] >= start_year) & (data["year"] <= end_year)]
                elif choice == '5':
                    data_filtered = data[data['fos'].apply(lambda x: any(f in x for f in fos_list) if isinstance(x, list) else False)]

                # Sauvegarder avec le bon format JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data_filtered.to_dict(orient='records'), f, indent=4)

                print(f"Fichier traité et enregistré sous : {output_path}")

if __name__ == "__main__":
    # Obtenir le chemin du répertoire du script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Chemin relatif du dossier source
    source_directory = os.path.join(current_dir, '..', 'Dataset', 'Split_nettoyé')
    # Chemin relatif du dossier de sortie
    output_directory = os.path.join(current_dir, '..', 'Dataset', 'Split_filtré')

    filter_files(source_directory, output_directory)





