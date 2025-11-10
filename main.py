"""
main.py
=======

Point d'entrée principal de l'application.

Ce module initialise la boucle événementielle asynchrone et affiche l'écran
de démarrage (Splash Screen) lors du lancement de l'application.

Dependencies:
    asyncio: Gestion des boucles événementielles asynchrones.
    qasync: Intégration entre asyncio et Qt.
    PySide6: Framework graphique pour l'interface utilisateur.
    pathlib: Gestion des chemins de fichiers.
"""

import asyncio
from pathlib import Path

import qasync
from PySide6.QtGui import QIcon
from qasync import QApplication

from SplashScreen import SplashScreen


def main() -> None:
    """Lance l'application en affichant l'écran de démarrage (Splash Screen).

    Initialise la boucle événementielle asynchrone `qasync` et démarre
    l'application PySide6.

    Returns:
        None
    """
    app = QApplication([])
    app.setWindowIcon(QIcon(str(Path.cwd() / "assets" / "icon.ico")))

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    splash = SplashScreen()
    splash.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    """Point d'exécution du programme."""
    main()
