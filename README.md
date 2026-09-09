# POS Reporting — Portage WLangage → Flask

## Contexte

Portage d'un module de reporting WinDev/WLangage (logiciel de caisse restauration)
vers Python/Flask, en conservant **exactement la même logique métier** que le
code d'origine (structures de données, agrégations, prompts IA).

L'application génère des analyses business automatiques (IA Gemini) à partir
des données de vente extraites de la caisse.

## Architecture

```
pos_reporting/
├── app/
│   ├── models.py               # Structures : Commande, LigneVente, Reglement
│   ├── config.py                # Clé API, liste des modèles IA (fallback)
│   ├── main.py                   # Routes Flask
│   ├── templates/index.html      # Interface web (bouton + affichage + PDF)
│   ├── services/
│   │   ├── data_loader.py        # Charge les commandes depuis le JSON caisse
│   │   ├── gemini_client.py      # Appel API Gemini + cascade de secours
│   │   ├── analyzers.py          # Les 10 fonctions d'analyse métier
│   │   ├── rapport.py             # Orchestration des 10 analyses
│   │   └── pdf_export.py          # Génération du PDF téléchargeable
│   └── logs/                      # Journal des erreurs / appels IA
├── data/Texte.json                # Données de test (599 commandes réelles)
├── Dockerfile + docker-compose.yml
├── diagnostic_api.py               # Script de diagnostic clé API / modèles
└── requirements.txt
```

## Les 10 analyses générées

1. Top & Flop Produits
2. Tendances et Jours Faibles
3. Paiements & Annulations
4. Heures de Pointe
5. Canaux de Vente
6. Origine des commandes
7. Performance par Utilisateur / Vendeur
8. Analyse par Caisse / Matériel
9. Cross-Selling / Paniers Associés
10. Prévision des Stocks

Chaque analyse agrège les données de vente, puis envoie le résultat à l'API
Gemini avec un prompt métier détaillé (rôle de consultant + structure de
réponse imposée). En cas d'échec (quota, modèle indisponible), l'app bascule
automatiquement sur le modèle suivant dans une liste de secours (~19 modèles).

## Lancer le projet en local

```bash
pip install -r requirements.txt
cp .env.example .env   # puis coller la clé GEMINI_API_KEY
python -m flask --app app.main run
```
Puis ouvrir http://127.0.0.1:5000

## Lancer avec Docker (portable sur n'importe quel serveur)

```bash
docker compose up --build
```

## Diagnostiquer un problème de clé API / modèles

```bash
python diagnostic_api.py
```
Liste les modèles réellement disponibles pour la clé et teste un appel réel.

## Problèmes rencontrés et résolus

| Symptôme | Cause identifiée | Solution |
|---|---|---|
| Sections de rapport vides | Erreurs non détaillées dans les logs | Ajout du code HTTP + message d'erreur Google dans les logs |
| Erreur 403 sur tous les modèles | Clé API invalide | Régénération de la clé |
| Erreur 429 "quota: 0" | Tier gratuit non actif sur certains modèles | Script de diagnostic pour identifier les modèles accessibles |
| Erreur 404 "no longer available" | Anciens modèles (2.0/2.5) fermés aux nouveaux comptes | Liste de modèles réordonnée avec les noms réellement disponibles |

## Roadmap (améliorations identifiées, non développées)

- Authentification simple sur la route de génération
- Historique des rapports générés (comparaison dans le temps)
- Filtrage par période (semaine / mois / dates personnalisées)
- Upload dynamique du fichier JSON depuis l'interface
- Déploiement effectif sur un serveur (VPS + Docker, une fois choisi)
