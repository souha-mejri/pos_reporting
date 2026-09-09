import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


LISTE_MODELES = [
    "gemini-flash-latest",
    "gemini-pro-latest",
    "gemini-flash-lite-latest",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    # anciens modèles en dernier recours (probablement bloqués pour ton compte)
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
]


TEMPS_ENTRE_REQ_MS = 1500

TIMEOUT_HTTP_MS = 360000 

# ==========================================
# Source des données de commandes
# ==========================================
# "local" -> lit data/Texte.json
# "url"   -> télécharge depuis DATA_URL (le lien donné par l'encadrant)
DATA_SOURCE_TYPE = os.environ.get("DATA_SOURCE_TYPE", "local")
DATA_URL = os.environ.get("DATA_URL", "")

# Heure (0-23) à laquelle le rapport complet est généré automatiquement chaque jour
HEURE_RAPPORT_QUOTIDIEN = int(os.environ.get("HEURE_RAPPORT_QUOTIDIEN", "6"))
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "")