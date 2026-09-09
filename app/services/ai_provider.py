"""
Point d'entrée UNIQUE utilisé par rapport.py pour appeler l'IA.
Redirige vers le fournisseur actif (réglable par l'admin, sans redémarrage).
"""

from app.db import get_parametre
from app.services import gemini_client, openai_client


def fournisseur_actif() -> str:
    return get_parametre("ai_provider", "gemini")


def generer_rapport_marketing(demande: str, users_texte: str) -> str:
    if fournisseur_actif() == "openai":
        return openai_client.generer_rapport_marketing(demande, users_texte)
    return gemini_client.generer_rapport_marketing(demande, users_texte)