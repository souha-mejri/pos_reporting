"""
Persistance des rapports générés automatiquement une fois par jour
(voir la tâche planifiée dans app/main.py).

Un rapport par jour est stocké dans data/rapports/AAAA-MM-JJ.json
"""

import json
from datetime import datetime
from pathlib import Path

REP_RAPPORTS = Path(__file__).resolve().parent.parent.parent / "data" / "rapports"
REP_RAPPORTS.mkdir(parents=True, exist_ok=True)


def sauvegarder_rapport(sections: list[dict], nombre_commandes: int, date: str | None = None) -> Path:
    date = date or datetime.now().strftime("%Y-%m-%d")
    chemin = REP_RAPPORTS / f"{date}.json"
    contenu = {
        "date": date,
        "genere_le": datetime.now().isoformat(timespec="seconds"),
        "nombre_commandes_analysees": nombre_commandes,
        "sections": sections,
    }
    with chemin.open("w", encoding="utf-8") as f:
        json.dump(contenu, f, ensure_ascii=False, indent=2)
    return chemin


def lister_dates_disponibles() -> list[str]:
    dates = [f.stem for f in REP_RAPPORTS.glob("*.json")]
    return sorted(dates, reverse=True)  # plus récent en premier


def charger_rapport(date: str) -> dict | None:
    chemin = REP_RAPPORTS / f"{date}.json"
    if not chemin.exists():
        return None
    with chemin.open("r", encoding="utf-8") as f:
        return json.load(f)


def comparer_rapports(date1: str, date2: str) -> dict | None:
    rapport1 = charger_rapport(date1)
    rapport2 = charger_rapport(date2)
    if rapport1 is None or rapport2 is None:
        return None

    sections1 = {section.get("titre", ""): section for section in rapport1.get("sections", [])}
    sections2 = {section.get("titre", ""): section for section in rapport2.get("sections", [])}
    titres = sorted(set(sections1) | set(sections2))

    return {
        "date1": date1,
        "date2": date2,
        "nombre_commandes_date1": rapport1.get("nombre_commandes_analysees"),
        "nombre_commandes_date2": rapport2.get("nombre_commandes_analysees"),
        "sections": [
            {
                "titre": titre,
                "date1": sections1.get(titre, {}).get("contenu"),
                "date2": sections2.get(titre, {}).get("contenu"),
            }
            for titre in titres
        ],
    }
