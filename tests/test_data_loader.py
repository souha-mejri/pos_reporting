from pathlib import Path

from app.services.data_loader import charger_commandes_lbms

FIXTURE = Path(__file__).resolve().parent.parent / "data" / "lbms_exemple.json"


def test_nombre_de_commandes_chargees():
    commandes = charger_commandes_lbms(FIXTURE)
    assert len(commandes) == 6


def test_mapping_commande_annulee_avec_produits():
    commandes = charger_commandes_lbms(FIXTURE)
    c = commandes[0]  # ID_AUTO 13566 : annulée, TYPCOM=3, 2 lignes de produits

    assert c.DateHeure == "20260717175559"  # DATE + Heure_Commande nettoyée
    assert c.Origine == "Caisse"
    assert c.ModeDeVente == "Livraison"     # TYPCOM=3
    assert c.MontantTotal == 48.1           # NETVEN
    assert c.CommandeAnnule is True
    assert c.caisse == "1"
    assert c.Utilisateur == "ADMIN"
    assert len(c.tabReg) == 0                # tabReglement vide sur cette commande
    assert len(c.Ligven) == 2
    assert c.Ligven[0].Nom == "REINE JUNIOR"
    assert c.Ligven[0].Qte == 1


def test_mapping_typcom_a_emporter():
    commandes = charger_commandes_lbms(FIXTURE)
    c = commandes[3]  # ID_AUTO 13828, TYPCOM=2
    assert c.ModeDeVente == "A emporter"


def test_mapping_typcom_sur_place():
    commandes = charger_commandes_lbms(FIXTURE)
    c = commandes[5]  # ID_AUTO 13898, TYPCOM=1
    assert c.ModeDeVente == "Sur place"


def test_mapping_plusieurs_reglements():
    commandes = charger_commandes_lbms(FIXTURE)
    c = commandes[4]  # ID_AUTO 13716 : payé en 2 fois (ES + CB)
    assert len(c.tabReg) == 2
    codes = {r.Reglement for r in c.tabReg}
    assert codes == {"ES", "CB"}