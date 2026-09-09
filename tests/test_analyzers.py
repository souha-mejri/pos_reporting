from pathlib import Path

from app.services.data_loader import charger_commandes_lbms
from app.services.analyzers import top_flop_produits, paiement_et_annulation
from app.services.rapport import TAB_LISTE_OP

FIXTURE = Path(__file__).resolve().parent.parent / "data" / "lbms_exemple.json"


def test_top_flop_produits_compte_les_quantites():
    commandes = charger_commandes_lbms(FIXTURE)
    _, users_texte = top_flop_produits(commandes)

    assert '"REINE JUNIOR": 1' in users_texte
    assert '"COCA COLA 33CL": 1' in users_texte
    assert '"MENU DOUBLE CHEESE BURGER": 1' in users_texte


def test_paiement_et_annulation_ignore_les_annulations_sans_reglement():
    commandes = charger_commandes_lbms(FIXTURE)
    _, users_texte = paiement_et_annulation(commandes)

    assert "Annulation:" not in users_texte
    assert '"Pas annulation"' in users_texte
    assert '"Qt": 5' in users_texte


def test_toutes_les_analyses_s_executent_sans_erreur():
    commandes = charger_commandes_lbms(FIXTURE)

    for slug, titre, fonction in TAB_LISTE_OP:
        demande, users_texte = fonction(commandes)
        assert demande, f"'demande' vide pour {slug}"
        assert users_texte, f"'users_texte' vide pour {slug}"