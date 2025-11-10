"""
update_manager.py
=================

Ce module permet de gérer la synchronisation des fichiers d'une application
avec un serveur distant via un manifest (hashs SHA256 des fichiers).

Fonctionnalités :
- Calcul du hash SHA256 local
- Téléchargement et sauvegarde du manifest
- Détection des fichiers manquants ou corrompus
- Téléchargement des fichiers nécessaires

Dependencies:
    aiohttp: Pour les requêtes HTTP asynchrones
    hashlib: Pour le calcul des empreintes SHA256
    json: Pour la lecture et l’écriture des fichiers manifest
    pathlib: Pour la gestion des chemins de fichiers
"""

# ------------------------------
# Imports
# ------------------------------

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Coroutine

import aiohttp
from aiohttp import ClientConnectorDNSError, ClientResponseError

from utils.Requests import Requests

# ------------------------------
# Constantes globales
# ------------------------------

MANIFEST_LOCAL = Path.cwd() / "manifest_local.json"
CLIENT_DIR = Path.cwd() / "app"


# ------------------------------
# Gestion des fichiers
# ------------------------------

def sha256_file(path: Path) -> str:
    """Calcule le hash SHA256 d’un fichier.

    Args:
        path (Path): Chemin du fichier dont il faut calculer le hash.

    Returns:
        str: Empreinte SHA256 hexadécimale du fichier.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------
# Gestion du manifest serveur
# ------------------------------

async def fetch_manifest(server_url: str) -> Coroutine[Any, Any, Any] | dict[str, str]:
    """Télécharge le manifest JSON depuis le serveur.

    Args:
        server_url (str): URL du serveur hébergeant le manifest.

    Returns:
        Coroutine | dict[str, str]: Le manifest récupéré ou un message d'erreur.
    """
    try:
        response = await Requests(server_url).get("")
        return response
    except ClientConnectorDNSError:
        return {"err": "DNS_ERROR"}
    except ClientResponseError as e:
        return {"err": f"{e}"}


def load_local_manifest() -> dict:
    """Charge le manifest local s’il existe.

    Returns:
        dict: Le manifest local chargé, ou un dictionnaire vide par défaut.
    """
    if MANIFEST_LOCAL.exists():
        with open(MANIFEST_LOCAL, "r") as f:
            return json.load(f)
    return {"files": {}}


def save_local_manifest(manifest: dict):
    """Sauvegarde le manifest local sur le disque.

    Args:
        manifest (dict): Le manifest à sauvegarder.
    """
    with open(MANIFEST_LOCAL, "w") as f:
        json.dump(manifest, f, indent=4, sort_keys=True)


# ------------------------------
# Gestion des différences de fichiers
# ------------------------------

def get_missing_or_corrupted_files(local_dir: Path, server_manifest: dict, local_manifest: dict) -> list[str]:
    """Renvoie la liste des fichiers à mettre à jour (manquants ou corrompus).

    Args:
        local_dir (Path): Dossier local contenant les fichiers.
        server_manifest (dict): Manifest distant contenant les empreintes SHA256.
        local_manifest (dict): Manifest local contenant les empreintes SHA256 locales.

    Returns:
        list[str]: Liste des chemins relatifs des fichiers à télécharger.
    """
    to_download = []
    for rel_path, server_hash in server_manifest["files"].items():
        file_path = local_dir / rel_path
        local_hash = local_manifest["files"].get(rel_path)
        if not file_path.exists() or sha256_file(file_path) != server_hash:
            to_download.append(rel_path)
    return to_download


# ------------------------------
# Téléchargement de fichiers
# ------------------------------

async def download_file(session: aiohttp.ClientSession, base_url: str, rel_path: str, dest: Path, progress_callback):
    """Télécharge un seul fichier avec suivi de progression.

    Args:
        session (aiohttp.ClientSession): Session HTTP asynchrone.
        base_url (str): URL de base du serveur.
        rel_path (str): Chemin relatif du fichier à télécharger.
        dest (Path): Dossier de destination local.
        progress_callback (Callable): Fonction appelée pour signaler la progression (0–100).
    """
    url = f"{base_url}/{rel_path}"
    dest_path = dest / rel_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    async with session.get(url) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0

        with open(dest_path, "wb") as f:
            async for chunk in resp.content.iter_chunked(64 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    progress = int(downloaded / total * 100)
                    await progress_callback(progress, rel_path)


async def download_missing_files(server_manifest: dict, to_download: list[str], local_dir: Path, progress_callback):
    """Télécharge uniquement les fichiers manquants ou modifiés.

    Args:
        server_manifest (dict): Manifest du serveur contenant les URLs de téléchargement.
        to_download (list[str]): Liste des fichiers à télécharger.
        local_dir (Path): Répertoire local où enregistrer les fichiers.
        progress_callback (Callable): Fonction appelée pour indiquer la progression globale.
    """
    total_files = len(to_download)
    if total_files == 0:
        return

    async with aiohttp.ClientSession() as session:
        for i, rel_path in enumerate(to_download, 1):
            await download_file(
                session,
                server_manifest["download_url"],
                rel_path,
                local_dir,
                lambda p, f=rel_path: progress_callback(
                    int((i - 1 + p / 100) / total_files * 100),
                    f
                )
            )
