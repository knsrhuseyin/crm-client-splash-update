"""
utils.py
========

Module utilitaire pour la gestion de l'affichage et du lancement du client CRM.

Ce module contient des fonctions d'aide pour :
    - Centrer une fenêtre PySide6 à l'écran.
    - Lancer le fichier exécutable du client.

Dependencies:
    subprocess: Exécution de processus externes.
    PySide6.QtGui: Accès à la géométrie de l'écran.
    pathlib: Gestion des chemins de fichiers.
"""

import subprocess
from pathlib import Path

from PySide6.QtGui import QGuiApplication

# =======================
# Configuration
# =======================
CLIENT_EXE = Path.cwd() / "app" / "CRMClient.exe"


def center_on_screen(self) -> None:
    """Centre une fenêtre sur l'écran principal.

    Cette fonction calcule les coordonnées nécessaires pour positionner
    une fenêtre PySide6 exactement au centre de l'écran.

    Args:
        self (QWidget): Instance de la fenêtre à centrer.
    """
    screen = QGuiApplication.primaryScreen().availableGeometry()
    x = (screen.width() - self.width()) // 2
    y = (screen.height() - self.height()) // 2
    self.move(x, y)


def launch_client() -> None:
    """Lance l'exécutable du client CRM.

    Lancement non bloquant du fichier `CRMClient.exe` depuis le dossier `app`.

    Raises:
        FileNotFoundError: Si le fichier exécutable n'existe pas.
    """
    if not CLIENT_EXE.exists():
        raise FileNotFoundError(f"Le fichier {CLIENT_EXE} est introuvable.")

    subprocess.Popen([str(CLIENT_EXE)])
