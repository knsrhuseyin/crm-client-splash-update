import aiohttp
import hashlib
import json
from pathlib import Path

MANIFEST_LOCAL = Path.cwd() / "manifest_local.json"
CLIENT_DIR = Path.cwd() / "app"


def sha256_file(path: Path) -> str:
    """Calcule le hash SHA256 d’un fichier."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


async def fetch_manifest(server_url: str) -> dict:
    """Télécharge le manifest JSON du serveur."""
    async with aiohttp.ClientSession() as session:
        async with session.get(server_url) as resp:
            resp.raise_for_status()
            return await resp.json()


def load_local_manifest() -> dict:
    """Charge le manifest local s’il existe."""
    if MANIFEST_LOCAL.exists():
        with open(MANIFEST_LOCAL, "r") as f:
            return json.load(f)
    return {"files": {}}


def save_local_manifest(manifest: dict):
    """Sauvegarde le manifest local."""
    with open(MANIFEST_LOCAL, "w") as f:
        json.dump(manifest, f, indent=4, sort_keys=True)


def get_missing_or_corrupted_files(local_dir: Path, server_manifest: dict, local_manifest: dict):
    """Renvoie la liste des fichiers à mettre à jour."""
    to_download = []
    for rel_path, server_hash in server_manifest["files"].items():
        file_path = local_dir / rel_path
        local_hash = local_manifest["files"].get(rel_path)
        if not file_path.exists() or sha256_file(file_path) != server_hash:
            to_download.append(rel_path)
    return to_download


async def download_file(session, base_url, rel_path, dest, progress_callback):
    """Télécharge un seul fichier avec suivi de progression."""
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


async def download_missing_files(server_manifest: dict, to_download: list, local_dir: Path, progress_callback):
    """Télécharge uniquement les fichiers manquants ou modifiés."""
    total_files = len(to_download)
    if total_files == 0:
        return

    async with aiohttp.ClientSession() as session:
        for i, rel_path in enumerate(to_download, 1):
            await download_file(session, server_manifest["download_url"], rel_path, local_dir,
                                lambda p, f=rel_path: progress_callback(int((i - 1 + p / 100) / total_files * 100), f))
