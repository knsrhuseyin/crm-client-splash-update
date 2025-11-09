import asyncio
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QProgressBar, QLabel, QVBoxLayout, QPushButton

from utils.update_manager import (fetch_manifest, load_local_manifest, get_missing_or_corrupted_files, download_missing_files, \
                                  save_local_manifest)
from utils.utils import launch_client, center_on_screen


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.label = None
        self.progress_bar = None
        self.layout = None
        self.button_reload = None
        self.button_close = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Chargement...")
        self.setFixedSize(300, 150)
        center_on_screen(self)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #222; color: white;")

        self.label = QLabel("Vérification des mises à jour...", alignment=Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size:14px; font-weight: bold;")
        self.label.setWordWrap(True)
        self.progress_bar = QProgressBar()

        self.button_reload = QPushButton("Réessayer")
        self.button_close = QPushButton("Fermer")
        self.button_reload.setVisible(False)
        self.button_close.setVisible(False)
        self.button_reload.clicked.connect(lambda: asyncio.create_task(self.check_for_update()))
        self.button_close.clicked.connect(self.close)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.button_reload)
        self.layout.addWidget(self.button_close)

        QTimer.singleShot(0, lambda: asyncio.create_task(self.check_for_update()))

    def error(self, text):
        self.label.setText(text)
        self.progress_bar.setVisible(False)
        self.button_reload.setVisible(True)
        self.button_close.setVisible(True)

    async def check_for_update(self):
        self.label.setText("Vérification des fichiers...")
        manifest_url = "https://api-crm.knsr-family.com/update/latest"

        # 1. Récupérer manifest serveur
        server_manifest = await fetch_manifest(manifest_url)
        local_manifest = load_local_manifest()

        # 2. Vérifier les fichiers manquants
        self.label.setText("Vérification des fichiers locaux...")
        to_download = get_missing_or_corrupted_files(Path("utils/app"), server_manifest, local_manifest)

        if to_download:
            self.label.setText(f"Téléchargement de \n{len(to_download)} fichier(s)...")

            async def progress(p, file):
                self.progress_bar.setValue(p)
                self.label.setText(f"Téléchargement des fichiers...\n{file}")

            await download_missing_files(server_manifest, to_download, Path("utils/app"), progress)

        # 3. Sauvegarde du manifest
        save_local_manifest(server_manifest)

        self.label.setText("Lancement de l'application...")
        self.progress_bar.setValue(100)
        await asyncio.sleep(0.3)
        launch_client()
        self.close()
