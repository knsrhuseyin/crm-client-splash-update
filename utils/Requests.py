"""
Requests.py
===========

Module contenant la classe `Requests` afin de faciliter l’envoi asynchrone de requêtes HTTP.

Ce module simplifie l’usage de `aiohttp` pour les requêtes GET, POST, PUT et DELETE,
et prend en charge le suivi de progression (progress_callback) lors des téléchargements.

Dependencies:
    aiohttp: Pour envoyer des requêtes HTTP asynchrones.
    asyncio: Pour la gestion des tâches asynchrones.
    json: Pour la lecture et l’écriture au format JSON.
"""

import asyncio
import json
from typing import Optional, Dict, Any, Callable

import aiohttp


class Requests:
    """Classe utilitaire pour faciliter l’envoi de requêtes HTTP asynchrones.

    Attributes:
        base_url (str): L’URL de base du serveur contenant l’API.
        headers (dict): Les en-têtes HTTP envoyés par défaut avec chaque requête.
    """

    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """Initialise un client HTTP asynchrone.

        Args:
            base_url (str): L’URL du serveur contenant l’API.
            headers (dict, optional): Les en-têtes HTTP à utiliser par défaut.
        """
        self.base_url = base_url.rstrip("/")
        self.headers = headers

    # ================================
    # Méthode interne générique
    # ================================

    async def _request(
        self,
        method: str,
        endpoint: str,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        **kwargs,
    ) -> Any:
        """Méthode interne gérant toutes les requêtes HTTP.

        Args:
            method (str): La méthode HTTP (GET, POST, PUT, DELETE).
            endpoint (str): Le chemin relatif de la requête.
            progress_callback (callable, optional): Fonction de rappel appelée
                pendant le téléchargement (pourcentage, nom du fichier).
            **kwargs: Autres arguments passés à `aiohttp.ClientSession.request()`.

        Returns:
            Any: Le corps de la réponse, parsé en JSON si possible, sinon texte brut.

        Raises:
            aiohttp.ClientResponseError: Si le code HTTP de la réponse indique une erreur.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.request(method, url, **kwargs) as response:

                # Vérifie si la requête a échoué (ex: 404, 500, etc.)
                if not response.ok:
                    try:
                        text = await response.json()
                    except aiohttp.ContentTypeError:
                        text = await response.text()

                    message = (
                        text.get("detail") if isinstance(text, dict) else str(text)
                    )
                    raise aiohttp.ClientResponseError(
                        status=response.status,
                        request_info=response.request_info,
                        history=response.history,
                        message=message,
                        headers=response.headers,
                    )

                # Suivi de progression
                total = int(response.headers.get("content-length", 0))
                data = bytearray()
                downloaded = 0

                if total and progress_callback:
                    progress_callback(0, endpoint)

                async for chunk in response.content.iter_chunked(64 * 1024):
                    data.extend(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total:
                        percentage = int(downloaded / total * 100)
                        progress_callback(percentage, endpoint)
                    await asyncio.sleep(0)

                if progress_callback and total:
                    progress_callback(100, endpoint)

                # Tentative de décodage JSON
                try:
                    return json.loads(data.decode())
                except Exception:
                    return data.decode()

    # ================================
    # Méthodes publiques
    # ================================

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Any:
        """Envoie une requête HTTP GET.

        Args:
            endpoint (str): URL de la ressource à interroger.
            params (dict, optional): Paramètres de la requête.
            headers (dict, optional): En-têtes HTTP personnalisés.
            progress_callback (callable, optional): Callback pour la progression.

        Returns:
            Any: Réponse de la requête.
        """
        return await self._request(
            "GET", endpoint, params=params, headers=headers, progress_callback=progress_callback
        )

    async def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Any:
        """Envoie une requête HTTP POST."""
        return await self._request(
            "POST", endpoint, data=data, json=json, headers=headers, progress_callback=progress_callback
        )

    async def put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Any:
        """Envoie une requête HTTP PUT."""
        return await self._request(
            "PUT", endpoint, json=json, headers=headers, progress_callback=progress_callback
        )

    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Any:
        """Envoie une requête HTTP DELETE."""
        return await self._request(
            "DELETE", endpoint, headers=headers, progress_callback=progress_callback
        )
