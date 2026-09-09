"""
Script de diagnostic à lancer directement :
    python diagnostic_api.py

Il ne dépend pas de Flask ni du reste du projet, pour isoler le problème.
Il fait 2 choses :
1. Appelle ListModels pour voir si la clé API est valide et récupérer la
   VRAIE liste des modèles disponibles pour ton compte (au lieu de deviner).
2. Si ça marche, tente un generateContent minimal sur le 1er modèle valide trouvé.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not API_KEY:
    print("❌ GEMINI_API_KEY est vide ou absent du fichier .env")
    exit(1)

print(f"Clé chargée : {API_KEY[:6]}...{API_KEY[-4:]} (longueur: {len(API_KEY)})")
print()

# ==========================================
# 1. ListModels : vérifie la clé + liste les modèles réellement disponibles
# ==========================================
print("=== Étape 1 : ListModels ===")
url_list = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
resp = requests.get(url_list, timeout=30)

print(f"Code retour : {resp.status_code}")

if resp.status_code != 200:
    print("Réponse Google :")
    print(resp.text[:2000])
    print()
    print("❌ La clé API ne fonctionne pas au niveau le plus basique.")
    print("   -> Vérifie sur https://aistudio.google.com/apikey que la clé est bien active")
    print("   -> Vérifie que le projet Google Cloud associé a l'API 'Generative Language API' activée")
    exit(1)

data = resp.json()
modeles = [m["name"].replace("models/", "") for m in data.get("models", [])
           if "generateContent" in m.get("supportedGenerationMethods", [])]

print(f"✅ Clé valide. {len(modeles)} modèles supportent generateContent :")
for m in modeles:
    print(f"   - {m}")
print()

if not modeles:
    print("❌ Aucun modèle disponible pour cette clé (ListModels a marché mais liste vide).")
    exit(1)

# ==========================================
# 2. Test réel sur le premier modèle disponible
# ==========================================
premier_modele = modeles[0]
print(f"=== Étape 2 : test generateContent sur '{premier_modele}' ===")

url_generate = f"https://generativelanguage.googleapis.com/v1beta/models/{premier_modele}:generateContent?key={API_KEY}"
payload = {
    "contents": [{"role": "user", "parts": [{"text": "Réponds juste 'ok'"}]}]
}
resp2 = requests.post(url_generate, json=payload, timeout=30)

print(f"Code retour : {resp2.status_code}")
if resp2.status_code == 200:
    texte = resp2.json()["candidates"][0]["content"]["parts"][0]["text"]
    print(f"✅ Ça fonctionne ! Réponse du modèle : {texte.strip()}")
    print()
    print(f"-> Mets '{premier_modele}' en premier dans LISTE_MODELES (app/config.py)")
else:
    print("Réponse Google :")
    print(resp2.text[:2000])
    print()
    print("❌ ListModels marche mais generateContent échoue -> probablement un souci de quota/billing.")
    print("   -> Va sur https://ai.dev/rate-limit pour voir ton quota réel")
    print("   -> Si le quota gratuit est à 0, il faut activer la facturation sur le projet Google Cloud")
