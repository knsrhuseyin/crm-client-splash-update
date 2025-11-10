"""
utils.py
========

Module utilitaire pour la gestion de l'affichage et du lancement du client CRM.

Fonctions fournies :
    - Centrer une fenêtre PySide6 à l'écran.
    - Lancer le fichier exécutable du client.

Dependencies:
    subprocess: Pour exécuter des processus externes.
    PySide6.QtGui: Accès à la géométrie de l'écran.
    PySide6.QtWidgets: Gestion des widgets.
    pathlib: Gestion des chemins de fichiers.
"""

import subprocess
from pathlib import Path

from PySide6.QtCore import QPoint
from PySide6.QtGui import QGuiApplication, Qt
from PySide6.QtWidgets import QLabel, QWidget

# =======================
# Configuration
# =======================
CLIENT_EXE = Path.cwd() / "app" / "CRMClient.exe"


class DraggableLabel(QLabel):
    """Label permettant de déplacer sa fenêtre parent par glisser-déposer.

    Attributes:
        drag_position (QPoint): Position du curseur relative au coin supérieur gauche
            de la fenêtre lors du clic de la souris.
    """

    def __init__(self, text: str, parent: QWidget) -> None:
        """Initialise le label draggable.

        Args:
            text (str): Texte affiché dans le label.
            parent (QWidget): Widget parent contenant le label.
        """
        super().__init__(text, parent)
        self.drag_position: QPoint = QPoint()
        self.setStyleSheet(
            "background-color: #3498db; color: white; padding: 10px;"
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event) -> None:
        """Gère le clic de la souris pour initier le déplacement.

        Args:
            event (QMouseEvent): Événement de clic de souris.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint()
                - self.window().frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        """Déplace la fenêtre si le bouton gauche de la souris est maintenu.

        Args:
            event (QMouseEvent): Événement de déplacement de la souris.
        """
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


def center_on_screen(widget: QWidget) -> None:
    """Centre une fenêtre sur l'écran principal.

    Cette fonction calcule les coordonnées nécessaires pour positionner
    une fenêtre PySide6 exactement au centre de l'écran.

    Args:
        widget (QWidget): Instance de la fenêtre à centrer.
    """
    screen = QGuiApplication.primaryScreen().availableGeometry()
    x = (screen.width() - widget.width()) // 2
    y = (screen.height() - widget.height()) // 2
    widget.move(x, y)


def launch_client() -> None:
    """Lance l'exécutable du client CRM.

    Lancement non bloquant du fichier `CRMClient.exe` depuis le dossier `app`.

    Raises:
        FileNotFoundError: Si le fichier exécutable n'existe pas.
    """
    if not CLIENT_EXE.exists():
        raise FileNotFoundError(f"Le fichier {CLIENT_EXE} est introuvable.")

    subprocess.Popen([str(CLIENT_EXE)])
