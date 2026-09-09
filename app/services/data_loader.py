"""
Équivalent WLangage :

    sDonneesJSON = fChargeTexte(CompléteRep(fRepExe)+"Texte.json")
    Désérialise(tabCommandeForamater, sDonneesJSON, psdJSON)
"""

import json
from pathlib import Path

import requests

from app.models import Commande, LigneVente, Reglement


# def charger_commandes(chemin_json: str | Path) -> list[Commande]:
 #    """
   #  Lit un fichier JSON LOCAL des commandes et retourne la liste des objets Commande.
   #  Équivalent de tabCommandeForamater en WLangage.
   #  """
   #  chemin_json = Path(chemin_json)

   #  with chemin_json.open("r", encoding="utf-8") as f:
    #     donnees_brutes = json.load(f)

    # return _commandes_depuis_liste(donnees_brutes)
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

# def charger_commandes_url(url: str, timeout: int = 30) -> list[Commande]:
  #   """
   #  Récupère le JSON des commandes depuis une URL
  #   """
   #  reponse = requests.get(url, timeout=timeout)
    # reponse.raise_for_status()  # lève une exception si code HTTP != 2xx
    # donnees_brutes = reponse.json()
    # return _commandes_depuis_liste(donnees_brutes)


def _commandes_depuis_liste(donnees_brutes: list[dict]) -> list[Commande]:
    tab_commande_formatees: list[Commande] = [
        Commande.from_dict(item) for item in donnees_brutes
    ]
    return tab_commande_formatees

MAPPING_TYPCOM = {
    1: "Sur place",
    2: "A emporter",
    3: "Livraison",
}


def _commande_depuis_lbms(item: dict) -> Commande:
    """
    Traduit un enregistrement brut du système LBMS vers notre objet Commande
    interne, pour que TOUTES les analyses (analyzers.py) continuent de
    fonctionner sans aucune modification.
    """
    info = item.get("INFORMATION_COMMANDE", {})

    date = item.get("DATE", "")
    heure_brute = info.get("Heure_Commande", "000000.000")  # ex: "17:55:59.200"
    heure_nettoyee = heure_brute.split(".")[0].replace(":", "")  # "175559"
    date_heure = f"{date}{heure_nettoyee}"

    typcom = info.get("TYPCOM")
    mode_vente = MAPPING_TYPCOM.get(typcom, f"Type {typcom}")

    tab_reg = [
        Reglement(
            Reglement=r.get("NomReglement") or r.get("Code", ""),
            Montant=r.get("MontantReglee", 0.0),
        )
        for r in info.get("tabReglement", [])
    ]

    ligven = [
        LigneVente(
            Nom=p.get("NomProduit", ""),
            Qte=p.get("Quantite", 0),
            Prix=p.get("moNetVente", 0.0),
        )
        for p in info.get("tabProduit", [])
    ]

    return Commande(
        DateHeure=date_heure,
        Origine=info.get("ORIGINE_COMMANDE", ""),
        ModeDeVente=mode_vente,
        # ⚠️ HYPOTHÈSE : NETVEN (montant net, après remise MONREM) plutôt que
        # MONVEN (montant brut). À confirmer selon ce que l'encadrant veut
        # analyser (CA encaissé réel vs CA affiché avant remise).
        MontantTotal=info.get("NETVEN", 0.0),
        CommandeAnnule=info.get("COMMANDE_ANNULER", False),
        caisse=item.get("CAISSE", ""),
        Utilisateur=item.get("CAISSIER", ""),
        tabReg=tab_reg,
        Ligven=ligven,
    )


def charger_commandes_lbms(source: str | Path) -> list[Commande]:
    """
    Charge les commandes au format LBMS, depuis un fichier local OU une URL
    (détection automatique : une source commençant par "http" est traitée
    comme une URL).
    """
    if isinstance(source, str) and source.startswith("http"):
        reponse = requests.get(source, timeout=30)
        reponse.raise_for_status()
        donnees_brutes = reponse.json()
    else:
        chemin = Path(source)
        with chemin.open("r", encoding="utf-8") as f:
            donnees_brutes = json.load(f)

    return [_commande_depuis_lbms(item) for item in donnees_brutes]
