"""
Équivalent WLangage de GenererRapportMarketing, avec cascade de secours entre
modèles. Différence par rapport à avant : la clé API est désormais lue
dynamiquement (base de données, modifiable par l'admin), avec repli sur .env
si rien n'est défini en base.
"""

import json
from datetime import datetime
from pathlib import Path

import requests

from app.config import LISTE_MODELES, TIMEOUT_HTTP_MS, GEMINI_API_KEY as GEMINI_API_KEY_ENV
from app.db import get_parametre

ModelUtilsee = LISTE_MODELES[0]
nDexModel = 0

REP_ERREUR = Path(__file__).resolve().parent.parent.parent / "app" / "logs"
REP_ERREUR.mkdir(parents=True, exist_ok=True)

RETENTION_JOURS = 7


def _purger_vieux_fichiers() -> None:
    seuil = datetime.now().timestamp() - (RETENTION_JOURS * 86400)
    for fichier in REP_ERREUR.glob("*"):
        try:
            if fichier.is_file() and fichier.stat().st_mtime < seuil:
                fichier.unlink()
        except OSError:
            pass


def traceut(message_err: str) -> None:
    nom_fichier = REP_ERREUR / f"{datetime.now().strftime('%Y%m%d')}.log"
    contenu = (
        "\n*****" + datetime.now().strftime("%H:%M:%S") + "*****\n"
        + "**********************\n" + message_err + "\n**********************\n\n\n"
    )
    with nom_fichier.open("a", encoding="utf-8") as f:
        f.write(contenu)


def _cle_api_active() -> str:
    """Clé Gemini active : celle définie par l'admin en base, sinon celle du .env."""
    return get_parametre("gemini_api_key") or GEMINI_API_KEY_ENV


def verification_etat_de_reponse(finish_reason: str) -> bool:
    return finish_reason == "STOP"


def generer_rapport_marketing(demande: str, users_texte: str) -> str:
    global ModelUtilsee, nDexModel

    cle_api = _cle_api_active()
    s_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{ModelUtilsee}:generateContent?key={cle_api}"
    )

    v_payload = {
        "system_instruction": {"parts": [{"text": demande}]},
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 32000},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
        "contents": [{"role": "user", "parts": [{"text": users_texte}]}],
    }

    try:
        ma_reponse = requests.post(
            s_url, headers={"Content-Type": "application/json"},
            data=json.dumps(v_payload), timeout=TIMEOUT_HTTP_MS / 1000,
        )
    except requests.exceptions.RequestException as e:
        traceut(f"Erreur réseau lors de l'appel à {ModelUtilsee} : {e}")
        if nDexModel < len(LISTE_MODELES) - 1:
            nDexModel += 1
            ModelUtilsee = LISTE_MODELES[nDexModel]
            return generer_rapport_marketing(demande, users_texte)
        return ""

    if ma_reponse.status_code == 200:
        v_resultat = ma_reponse.json()
        try:
            finish_reason = v_resultat["candidates"][0]["finishReason"]
        except (KeyError, IndexError):
            finish_reason = "AUTRES CAS"

        if verification_etat_de_reponse(finish_reason):
            return v_resultat["candidates"][0]["content"]["parts"][0]["text"]
        if nDexModel < len(LISTE_MODELES) - 1:
            nDexModel += 1
            ModelUtilsee = LISTE_MODELES[nDexModel]
            return generer_rapport_marketing(demande, users_texte)
        return ""

    traceut(f"Code {ma_reponse.status_code} pour le modèle {ModelUtilsee}\nRéponse Google : {ma_reponse.text[:1000]}")
    if nDexModel < len(LISTE_MODELES) - 1:
        nDexModel += 1
        ModelUtilsee = LISTE_MODELES[nDexModel]
        return generer_rapport_marketing(demande, users_texte)
    return ""


def reset_fallback_modele() -> None:
    global ModelUtilsee, nDexModel
    nDexModel = 0
    ModelUtilsee = LISTE_MODELES[0]


def list_models() -> list[str]:
    return LISTE_MODELES


def get_current_model() -> str:
    return ModelUtilsee


def set_current_model(model: str) -> None:
    global ModelUtilsee, nDexModel
    if model not in LISTE_MODELES:
        raise ValueError(f"Modèle inconnu : {model}")
    ModelUtilsee = model
    nDexModel = LISTE_MODELES.index(model)