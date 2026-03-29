import os
from lxml import etree

def fix_gexf_file(input_path, output_path):
    try:
        # Lire et parser le fichier GEXF en entier
        parser = etree.XMLParser(recover=True)
        tree = etree.parse(input_path, parser)
        
        # Écrire le fichier corrigé
        with open(output_path, 'wb') as outfile:
            tree.write(outfile, encoding='utf-8', pretty_print=True, xml_declaration=True)
        print(f"Le fichier GEXF corrigé a été enregistré sous : {output_path}")
    except etree.XMLSyntaxError as e:
        print(f"Erreur de syntaxe XML lors de la lecture du fichier GEXF : {e}")

if __name__ == "__main__":
    # Obtenir le chemin du répertoire du script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Chemins relatifs vers le fichier GEXF original et corrigé
    original_path = os.path.join(current_dir, '..', 'Dataset', 'Graphe', 'merged_top_1000_2_collaboration_network.gexf')
    fixed_path = os.path.join(current_dir, '..', 'Dataset', 'Graphe', 'merged_top_1000_2_collaboration_network_fixed.gexf')

    # Corriger le fichier GEXF
    fix_gexf_file(original_path, fixed_path)
