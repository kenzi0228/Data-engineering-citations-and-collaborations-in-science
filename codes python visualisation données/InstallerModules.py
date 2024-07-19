import subprocess
import sys

# Liste des modules à installer
modules = [
    "pandas",
    "networkx",
    "community",
    "matplotlib",
    "tqdm",
    "lxml"
]

def install_modules(modules):
    for module in modules:
        subprocess.check_call([sys.executable, "-m", "pip", "install", module])

if __name__ == "__main__":
    install_modules(modules)
    print("Tous les modules nécessaires ont été installés.")


