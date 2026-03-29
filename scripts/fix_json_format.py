import os

def check_and_fix_json(file_path):
    needs_bracket_open = False
    needs_bracket_close = False

    with open(file_path, 'r', encoding='utf-8') as file:
        first_line = file.readline().strip()
        if not first_line.startswith('['):
            needs_bracket_open = True

    with open(file_path, 'r+', encoding='utf-8') as file:
        file.seek(0, os.SEEK_END)
        file.seek(file.tell() - 1024, os.SEEK_SET)  # Reculer de 1024 bytes pour être sûr de capturer la dernière ligne
        last_lines = file.readlines()
        last_line = last_lines[-1].strip() if last_lines else ''
        if not last_line.endswith(']'):
            needs_bracket_close = True

    # Réécrire le fichier si nécessaire
    if needs_bracket_open or needs_bracket_close:
        with open(file_path, 'r+', encoding='utf-8') as file:
            content = file.read()
            if needs_bracket_open:
                content = '[' + content.lstrip()
            if needs_bracket_close:
                content = content.rstrip() + ']'
            file.seek(0)
            file.write(content)
            file.truncate()  # Tronquer le fichier pour supprimer l'ancien contenu si la nouvelle longueur est inférieure
        print(f"Le fichier {os.path.basename(file_path)} a été mis à jour.")
    else:
        print(f"Le fichier {os.path.basename(file_path)} est déjà correct.")

if __name__ == "__main__":
    # Obtenir le chemin du répertoire du script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Chemin relatif du dossier contenant les fichiers JSON
    directory_path = os.path.join(current_dir, '..', 'Dataset', 'Split_prétraité')

    # Liste tous les fichiers dans le dossier
    files = [file for file in os.listdir(directory_path) if file.endswith('.json')]

    # Parcourir chaque fichier
    for file_name in files:
        file_path = os.path.join(directory_path, file_name)
        check_and_fix_json(file_path)

    print("Vérification et mise à jour terminées.")

