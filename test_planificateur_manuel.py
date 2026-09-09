"""
Teste manuellement ce que fait le planificateur, sans attendre 6h du matin.
⚠️ Ça appelle réellement Gemini sur les 10 catégories (~15-30s, consomme du quota).

Usage :
    python test_planificateur_manuel.py
"""

import sys
sys.path.insert(0, ".")

from app.main import scheduler, _tache_quotidienne
from app.services import historique

# On coupe le vrai planificateur : on ne veut que l'appel manuel ici,
# pas qu'il se déclenche aussi tout seul en tâche de fond pendant le test.
scheduler.shutdown(wait=False)

print("Lancement manuel de _tache_quotidienne() (identique à ce que fait le cron)...")
_tache_quotidienne()

print("\nVérification de l'historique :")
dates = historique.lister_dates_disponibles()
print("Dates disponibles :", dates)

if dates:
    rapport = historique.charger_rapport(dates[0])
    print(f"\nRapport du {rapport['date']} :")
    print(f"  {rapport['nombre_commandes_analysees']} commandes analysées")
    print(f"  {len(rapport['sections'])} sections générées")
    for s in rapport["sections"]:
        apercu = (s["contenu"][:60] + "...") if s["contenu"] else "(VIDE)"
        print(f"  - {s['titre']}: {apercu}")
else:
    print("❌ Aucun fichier créé dans data/rapports/ — vérifie app/logs/ pour l'erreur.")