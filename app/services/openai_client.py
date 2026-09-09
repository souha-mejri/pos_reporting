"""
Deuxième fournisseur IA, activable depuis le panneau admin.
Même logique que gemini_client.py : cascade entre modèles, clé lue
dynamiquement (admin > .env).
"""

import json
from datetime import datetime
from pathlib import Path

import requests

from app.db import get_parametre

LISTE_MODELES_OPENAI = ["gpt-4o-mini", "gpt-4o"]

REP_ERREUR = Path(__file__).resolve().parent.parent.parent / "app" / "logs"
REP_ERREUR.mkdir(parents=True, exist_ok=True)

ModelUtilsee = LISTE_MODELES_OPENAI[0]
nDexModel = 0


def traceut(message_err: str) -> None:
    nom_fichier = REP_ERREUR / f"{datetime.now().strftime('%Y%m%d')}.log"
    with nom_fichier.open("a", encoding="utf-8") as f:
        f.write(f"\n*****{datetime.now().strftime('%H:%M:%S')}*****\n{message_err}\n\n")


def _cle_api_active() -> str:
    return get_parametre("openai_api_key") or ""


def generer_rapport_marketing(demande: str, users_texte: str) -> str:
    global ModelUtilsee, nDexModel

    cle_api = _cle_api_active()
    if not cle_api:
        traceut("Aucune clé OpenAI configurée (ni en base, ni dans .env).")
        return ""

    payload = {
        "model": ModelUtilsee,
        "messages": [
            {"role": "system", "content": demande},
            {"role": "user", "content": users_texte},
        ],
        "temperature": 0.2,
    }

    try:
        reponse = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {cle_api}", "Content-Type": "application/json"},
            data=json.dumps(payload), timeout=120,
        )
    except requests.exceptions.RequestException as e:
        traceut(f"Erreur réseau OpenAI ({ModelUtilsee}) : {e}")
        return _basculer_modele_suivant(demande, users_texte)

    if reponse.status_code == 200:
        return reponse.json()["choices"][0]["message"]["content"]

    traceut(f"Code {reponse.status_code} pour le modèle OpenAI {ModelUtilsee}\n{reponse.text[:1000]}")
    return _basculer_modele_suivant(demande, users_texte)


def _basculer_modele_suivant(demande: str, users_texte: str) -> str:
    global ModelUtilsee, nDexModel
    if nDexModel < len(LISTE_MODELES_OPENAI) - 1:
        nDexModel += 1
        ModelUtilsee = LISTE_MODELES_OPENAI[nDexModel]
        return generer_rapport_marketing(demande, users_texte)
    return ""