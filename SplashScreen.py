"""
SplashScreen.py
===============

Module définissant la fenêtre de démarrage (Splash Screen) de l'application.

Ce module gère la vérification des mises à jour, le téléchargement des fichiers manquants,
et le lancement du client une fois l'application prête.

Dependencies:
    asyncio: Gestion asynchrone des tâches.
    PySide6: Création et affichage de l'interface graphique.
    pathlib: Gestion des chemins de fichiers.
    utils.update_manager: Gestion des mises à jour et des manifests.
    utils.utils: Fonctions utilitaires (centrage, lancement du client, etc.).
"""

import asyncio
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QProgressBar, QLabel, QVBoxLayout, QPushButton

from utils.update_manager import (
    fetch_manifest,
    load_local_manifest,
    get_missing_or_corrupted_files,
    download_missing_files,
    save_local_manifest,
)
from utils.utils import launch_client, center_on_screen, DraggableLabel


class SplashScreen(QWidget):
    """Écran de chargement initial du programme.

    Affiche la progression de la vérification et du téléchargement des mises à jour
    avant le lancement du client.
    """

    def __init__(self) -> None:
        """Initialise le Splash Screen et configure l'interface utilisateur."""
        super().__init__()
        self.label: QLabel | None = None
        self.progress_bar: QProgressBar | None = None
        self.layout: QVBoxLayout | None = None
        self.button_reload: QPushButton | None = None
        self.button_close: QPushButton | None = None
        self.author_label: DraggableLabel | None = None
        self.init_ui()

    def init_ui(self) -> None:
        """Configure et initialise les composants graphiques du Splash Screen."""
        self.setWindowTitle("Chargement...")
        self.setFixedSize(300, 150)
        center_on_screen(self)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet("background-color: #222; color: white;")

        self.label = QLabel(
            "Vérification des mises à jour...", alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.label.setStyleSheet("font-size:14px; font-weight: bold;")
        self.label.setWordWrap(True)

        self.progress_bar = QProgressBar()

        self.button_reload = QPushButton("Réessayer")
        self.button_close = QPushButton("Fermer")
        self.button_reload.setVisible(False)
        self.button_reload.clicked.connect(
            lambda: asyncio.create_task(self.check_for_update())
        )
        self.button_close.clicked.connect(self.close)

        self.author_label = DraggableLabel(
            "CRM Splash | Created by knsrhuseyin | Version 1.0", self
        )
        self.author_label.setStyleSheet("font-size: 12px; color: gray;")
        self.author_label.setFixedHeight(30)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 10)
        self.layout.setSpacing(2)
        self.layout.addWidget(self.author_label)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.button_reload)
        self.layout.addWidget(self.button_close)

        # Lancement de la vérification des mises à jour dès l'ouverture
        QTimer.singleShot(0, lambda: asyncio.create_task(self.check_for_update()))

    def error(self, text: str, error: bool = True) -> None:
        """Affiche un message d'erreur ou rétablit l'affichage normal.

        Args:
            text (str): Message à afficher sur l'écran.
            error (bool): Si True, affiche le bouton "Réessayer".
        """
        self.label.setText(text)
        self.progress_bar.setVisible(not error)
        self.button_reload.setVisible(error)

    async def check_for_update(self) -> None:
        """Vérifie les mises à jour et télécharge les fichiers manquants si nécessaire.

        Étapes :
            1. Récupère le manifest distant.
            2. Compare avec le manifest local.
            3. Télécharge les fichiers manquants ou corrompus.
            4. Sauvegarde le manifest mis à jour.
            5. Lance le client.
        """
        self.error("Vérification des fichiers...", False)
        manifest_url = "https://api-crm.knsr-family.com/update/latest"

        # 1. Récupération du manifest serveur
        server_manifest = await fetch_manifest(manifest_url)
        if "err" in server_manifest:
            if server_manifest["err"] == "DNS_ERROR":
                self.error("Erreur de connexion\nVérifiez votre connexion internet !")
                return

        # 2. Chargement du manifest local
        local_manifest = load_local_manifest()

        # 3. Vérification des fichiers locaux
        self.label.setText("Vérification des fichiers locaux...")
        to_download = get_missing_or_corrupted_files(
            Path.cwd(), server_manifest, local_manifest
        )

        if to_download:
            self.label.setText(f"Téléchargement de \n{len(to_download)} fichier(s)...")

            async def progress(p: int, file: str) -> None:
                """Met à jour la barre de progression pendant le téléchargement."""
                self.progress_bar.setValue(p)
                self.label.setText(f"Téléchargement des fichiers...\n{file}")

            await download_missing_files(server_manifest, to_download, Path.cwd(), progress)

        # 4. Sauvegarde du manifest mis à jour
        save_local_manifest(server_manifest)

        # 5. Lancement du client
        self.label.setText("Lancement de l'application...")
        self.progress_bar.setValue(100)
        await asyncio.sleep(0.2)
        launch_client()
        self.close()
