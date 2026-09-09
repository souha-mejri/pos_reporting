"""
Équivalent WLangage de la boucle principale (bouton btn_rapport) :

    tabListeOp est tableau de chaîne = ["Top & Flop Produits", ...]
    tabListeProcedure est tableau de chaîne = ["TopFlopProduits", ...]
    sRapportFinal est chaîne

    POUR nDice = 1 à tabListeOp..Occurrence
        Multitâche(10)
        LIB_numOp = nDice+"/"+Maxop
        AjouteeTexte(tabListeOp[nDice], "Arial", Vrai, 14, chCentre)
        ExécuteTraitement(tabListeProcedure[nDice], trtProcédure, Demande, UsersTexte)
        sRapportFinal = GenererRapportMarketing(Demande, UsersTexte)
        AjouteeTexte(sRapportFinal, "Arial", Faux, 10, chGauche)
        Multitâche(TempsEntreREQ)
    FIN
    BT_IMPRIMER1..Visible = Vrai
"""

import time

from app.models import Commande
from app.config import TEMPS_ENTRE_REQ_MS
from app.services import analyzers
from app.services.gemini_client import generer_rapport_marketing, _purger_vieux_fichiers

# tabListeOp (titres affichés) <-> tabListeProcedure (fonctions), dans le même ordre
# "slug" = identifiant stable (utilisé par l'API / les cases à cocher), qui ne
# change pas même si on retraduit ou modifie le titre affiché.
TAB_LISTE_OP = [
    ("top_flop", "Top & Flop Produits", analyzers.top_flop_produits),
    ("tendances", "Tendances et Jours Faibles", analyzers.tendance_et_jours_faible),
    ("paiements", "Paiements & Annulations", analyzers.paiement_et_annulation),
    ("heures_pointe", "Heures de Pointe", analyzers.heure_de_pointe),
    ("canaux_vente", "Canaux de Ventes", analyzers.caneaux_de_vente),
    ("origine", "origine", analyzers.origine_commande),
    ("performance_utilisateur", "Performance par Utilisateur / Vendeur", analyzers.perfermonce_par_utilisateur),
    ("performance_caisse", "Analyse par Caisse / Matériel", analyzers.analyse_par_caisse),
    ("cross_selling", "Cross-Selling / Paniers Associés", analyzers.panier_associe),
    ("prevision_stocks", "Prévision des Stocks / Prep", analyzers.prevision_des_stocks),
]


def liste_categories() -> list[dict]:
    """Pour alimenter les cases à cocher côté front-end : [{"slug":..., "titre":...}, ...]"""
    return [{"slug": slug, "titre": titre} for slug, titre, _ in TAB_LISTE_OP]


def generer_rapport_complet(
    commandes: list[Commande],
    categories: list[str] | None = None,
    progress_callback=None,
) -> list[dict]:
    """
    Équivalent de la boucle principale du bouton btn_rapport.

    categories : liste de slugs (ex: ["heures_pointe", "top_flop"]) pour ne
    lancer qu'un sous-ensemble des 10 analyses. None ou liste vide -> les 10.

    progress_callback(nDice, maxop, titre) : optionnel, appelé à chaque itération
    (équivalent de LIB_numOp = nDice+"/"+Maxop pour afficher la progression).

    Retourne une liste de sections (équivalent du contenu accumulé dans
    sRapportFinal / SAI_Texte_RTF via AjouteeTexte) :
        [{"slug": "...", "titre": "...", "contenu": "..."}, ...]
    """
    if categories:
        categories_set = set(categories)
        operations = [op for op in TAB_LISTE_OP if op[0] in categories_set]
    else:
        operations = TAB_LISTE_OP

    maxop = len(operations)
    sections: list[dict] = []

    _purger_vieux_fichiers()  # ménage dans app/logs/ avant de commencer

    for n_dice, (slug, titre_op, fonction_analyse) in enumerate(operations, start=1):
        # Multitâche(10) -> petite pause, négligeable, gardée pour fidélité
        time.sleep(0.01)

        if progress_callback:
            progress_callback(n_dice, maxop, titre_op)

        # AjouteeTexte(tabListeOp[nDice], "Arial", Vrai, 14, chCentre)
        # -> titre de section (Arial, Gras, 14, centré)

        # ExécuteTraitement(tabListeProcedure[nDice], trtProcédure, Demande, UsersTexte)
        demande, users_texte = fonction_analyse(commandes)

        # sRapportFinal = GenererRapportMarketing(Demande, UsersTexte)
        s_rapport_final = generer_rapport_marketing(demande, users_texte)

        # AjouteeTexte(sRapportFinal, "Arial", Faux, 10, chGauche)
        # -> contenu de section (Arial, normal, 10, gauche)
        sections.append({
            "slug": slug,
            "titre": titre_op,
            "contenu": s_rapport_final,
        })

        # Multitâche(TempsEntreREQ)
        time.sleep(TEMPS_ENTRE_REQ_MS / 1000)

    # BT_IMPRIMER1..Visible = Vrai
    # -> équivalent : le rapport est prêt à être exporté/imprimé (voir route Flask)

    return sections