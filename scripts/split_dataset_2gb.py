import os
import json

# Obtenir le chemin du répertoire du script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Chemin relatif vers le fichier d'entrée
input_path = os.path.join(current_dir, '..', 'Dataset', 'Dataset publication scientifique JSON.json')
# Chemin de base relatif pour les fichiers de sortie
base_output_path = os.path.join(current_dir, '..', 'Dataset', 'Split_')

def split_json_file(input_path, base_output_path, chunk_size=2 * 10**9):
    with open(input_path, 'r', encoding='utf-8') as big_file:
        file_count = 1
        current_file = open(f'{base_output_path}{file_count}.json', 'w', encoding='utf-8')
        current_file.write('[')  # Ouvrir la balise JSON pour le premier fichier
        current_size = 0
        first_record = True

        for line in big_file:
            record_size = len(line.encode('utf-8'))
            # Vérifier si ajouter cette ligne dépasserait la taille de chunk_size
            if current_size + record_size > chunk_size:
                current_file.write(']')  # Fermer la balise JSON pour le fichier actuel
                current_file.close()
                file_count += 1
                current_file = open(f'{base_output_path}{file_count}.json', 'w', encoding='utf-8')
                current_file.write('[')  # Ouvrir la balise JSON pour le nouveau fichier
                current_size = 0
                first_record = True  # Réinitialiser le drapeau pour le premier enregistrement

            # Ajouter une virgule avant chaque enregistrement sauf le premier
            if not first_record:
                current_file.write(',\n')
            else:
                first_record = False

            current_file.write(line.strip())
            current_size += record_size

        current_file.write(']')  # Fermer la balise JSON pour le dernier fichier
        current_file.close()

split_json_file(input_path, base_output_path)

print("Splitting completed.")
