import re
import os

def preprocess_json(input_path, output_path):
    # Expression régulière pour trouver "NumberInt(x)" et le remplacer par "x"
    pattern = re.compile(r'NumberInt\((\d+)\)')

    with open(input_path, 'r', encoding='utf-8') as input_file, \
         open(output_path, 'w', encoding='utf-8') as output_file:
        for line in input_file:
            # Remplacer "NumberInt(x)" par "x"
            new_line = pattern.sub(r'\1', line)
            output_file.write(new_line)

# Obtenir le chemin du répertoire du script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Chemin relatif pour les fichiers d'entrée et de sortie
base_input_path = os.path.join(current_dir, '..', 'Dataset', 'Split Standart', 'Split_{}_Standart.json')
base_output_path = os.path.join(current_dir, '..', 'Dataset', 'Split_prétraité', 'Split_{}_prétraité.json')

# Boucler sur les fichiers de 1 à 9
for i in range(1, 10):
    input_json_path = base_input_path.format(i)
    processed_json_path = base_output_path.format(i)
    preprocess_json(input_json_path, processed_json_path)
    print(f"Le fichier {input_json_path} a été prétraité pour remplacer les 'NumberInt' par des entiers standards.")
