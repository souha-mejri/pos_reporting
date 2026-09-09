"""
Équivalent Python des Structures WLangage :
- StReglement
- Ligven
- StCommande

On garde volontairement les mêmes noms de champs que dans le JSON / WLangage
(Nom, Qte, Prix, DateHeure, Origine, ModeDeVente, MontantTotal, CommandeAnnule,
caisse, Utilisateur, tabReg, Ligven) pour éviter toute ambiguïté de mapping
avec le code d'origine.
"""

from dataclasses import dataclass, field


@dataclass
class Reglement:
    # StReglement est une Structure
    Reglement: str = ""      # ex: "Especes", "CB", "Sans contact", "Ticket Resto"
    Montant: float = 0.0


@dataclass
class LigneVente:
    # Ligven est une Structure
    Nom: str = ""
    Qte: int = 0
    Prix: float = 0.0


@dataclass
class Commande:
    # StCommande est une Structure
    DateHeure: str = ""              # format "AAAAMMJJHHMMSS" ex: "20260623110500"
    Origine: str = ""                # "Caisse", "Borne", ...
    ModeDeVente: str = ""            # "Sur place", "A emporter", "Livraison"
    MontantTotal: float = 0.0
    CommandeAnnule: bool = False
    caisse: str = ""
    Utilisateur: str = ""
    tabReg: list[Reglement] = field(default_factory=list)
    Ligven: list[LigneVente] = field(default_factory=list)

    @staticmethod
    def from_dict(d: dict) -> "Commande":
        return Commande(
            DateHeure=d.get("DateHeure", ""),
            Origine=d.get("Origine", ""),
            ModeDeVente=d.get("ModeDeVente", ""),
            MontantTotal=d.get("MontantTotal", 0.0),
            CommandeAnnule=d.get("CommandeAnnule", False),
            caisse=d.get("caisse", ""),
            Utilisateur=d.get("Utilisateur", ""),
            tabReg=[Reglement(**r) for r in d.get("tabReg", [])],
            Ligven=[LigneVente(**l) for l in d.get("Ligven", [])],
        )
