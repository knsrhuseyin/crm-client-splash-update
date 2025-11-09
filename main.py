import asyncio
from pathlib import Path

import qasync
from PySide6.QtGui import QIcon
from qasync import QApplication

from SplashScreen import SplashScreen


def main():
    """
    Fonction principale permettant l'ouverture de l'application en ouvrant le Splash Screen.
    """
    app = QApplication([])
    app.setWindowIcon(QIcon(str(Path(Path.cwd() / "assets" / "icon.ico"))))
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    splash = SplashScreen()
    splash.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    """Lancement du programme"""
    main()
