import subprocess
from pathlib import Path

from PySide6.QtGui import QGuiApplication

CLIENT_EXE = Path.cwd() / "app" / "CRMClient.exe"


def center_on_screen(self):
    """
    Fonction permettant de centrer la page sur l'écran
    """
    screen = QGuiApplication.primaryScreen().availableGeometry()
    x = (screen.width() - self.width()) // 2
    y = (screen.height() - self.height()) // 2
    self.move(x, y)


def launch_client():
    """Lance l'application .exe du client."""
    if not CLIENT_EXE.exists():
        raise FileNotFoundError(f"Le fichier {CLIENT_EXE} est introuvable")

    # Lancement de l'exe, non bloquant
    subprocess.Popen([str(CLIENT_EXE)])
