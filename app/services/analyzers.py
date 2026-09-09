"""
Équivalent WLangage des procédures d'analyse métier.
Chaque fonction reproduit EXACTEMENT la même logique d'agrégation
que sa procédure WLangage d'origine (mêmes boucles, mêmes clés de
regroupement), et retourne le même couple (Demande, UsersTexte)
qui sera envoyé à generer_rapport_marketing().

tabCommandeForamater (global WLangage) devient le paramètre `commandes`
(liste de app.models.Commande) passé explicitement à chaque fonction.
"""

import json

from app.models import Commande


# ==========================================================
# 1. TopFlopProduits
# ==========================================================
def top_flop_produits(commandes: list[Commande]) -> tuple[str, str]:
    """
    Équivalent PROCÉDURE TopFlopProduits(Demande, UsersTexte)
    """
    # tabListeProduit est tableau associatif d'entiers
    tab_liste_produit: dict[str, int] = {}

    for commande in commandes:
        for ligne in commande.Ligven:
            tab_liste_produit[ligne.Nom] = tab_liste_produit.get(ligne.Nom, 0) + ligne.Qte

    # Sérialise(tabListeProduit, TexteASerialsie, psdJSON)
    texte_a_serialiser = json.dumps(tab_liste_produit, ensure_ascii=False)

    # --- VARIABLE 1 : System Instruction ---
    demande = """
Tu es un consultant expert en gestion de restaurants et en Business Intelligence. Ton objectif est d'analyser les données de vente pour aider le gérant à maximiser son chiffre d'affaires et sa rentabilité.
RÈGLES DE RÉDACTION STRICTES :
- Garde un ton strictement professionnel, neutre et analytique. Ne joue pas de rôle théâtral et n'utilise JAMAIS de phrases familières, d'ordres ou de tutoiement.
- Parle "business" et "performance" (analyse du mix produit, marge contributive, ticket moyen, volume de vente).
- Sois  professionnel ,direct, factuel et orienté vers des solutions rentables.
- Organise ta réponse de manière très visuelle avec des titres clairs (###) et des puces (-).
- Approfondis tes solutions : explique concrètement comment optimiser la carte (le menu) dès demain sur la base des résultats.
"""

    # --- VARIABLE 2 : Content ---
    users_texte = """
Voici les données de ventes extraites du logiciel de caisse (POS).

CONSIGNES DE TRAITEMENT :
- Exclus les suppléments, sauces, options de cuisson et les erreurs de caisse (produits à 1 ou 2 ventes) de ton analyse principale. Base-toi uniquement sur les vrais plats, menus ou boissons.

MISSION SPÉCIFIQUE :
1- Identifie clairement le TOP 3 (Les Stars) et le FLOP 3 (Les Poids Morts).
2- Propose exactement 2 actions marketing immédiates et chirurgicales basées sur ces Tops et Flops (ex: offres combinées, mise en avant sur borne, suppression).
3- Rédige une conclusion courte et motivante pour encourager le gérant.

Données des ventes :
""" + texte_a_serialiser

    return demande, users_texte


# ==========================================================
# 2. TendanceEtJoursFaible
# ==========================================================
def tendance_et_jours_faible(commandes: list[Commande]) -> tuple[str, str]:
    """
    Équivalent PROCÉDURE TendanceEtJoursFaible(Demande, UsersTexte)
    """
    # tabCommandeJours est tableau associatif de StInf (ici: dict de dicts {nom, Montant, Qt})
    tab_commande_jours: dict[str, dict] = {}

    for commande in commandes:
        if commande.CommandeAnnule == False:
            jours_ut = commande.DateHeure[:8]  # Gauche(DateHeure, 8)

            if jours_ut not in tab_commande_jours:
                tab_commande_jours[jours_ut] = {"nom": jours_ut, "Montant": 0.0, "Qt": 0}

            tab_commande_jours[jours_ut]["nom"] = jours_ut
            tab_commande_jours[jours_ut]["Montant"] += commande.MontantTotal
            tab_commande_jours[jours_ut]["Qt"] += 1

    # FOR EACH elemnt OF tabCommandeJours ... sResume += elemnt.nom+"->Qt="+elemnt.Qt+",CA-->"+elemnt.Montant+RC
    s_resume = ""
    for elemnt in tab_commande_jours.values():
        s_resume += f"{elemnt['nom']}->Qt={elemnt['Qt']},CA-->{elemnt['Montant']}\n"

    # --- VARIABLE 1 : System Instruction ---
    demande = """
Tu es un consultant expert en gestion de restaurants et en stratégie de croissance. Ton objectif est d'analyser le rythme hebdomadaire de la clientèle pour aider le gérant à optimiser sa planification et son chiffre d'affaires.
RÈGLES DE RÉDACTION STRICTES :
- Garde un ton strictement professionnel, analytique et stratégique. Ne joue pas de rôle théâtral et n'utilise aucune expression familière ou tutoiement.
- Parle "business" et "stratégie" (cycle hebdomadaire, flux de clientèle, rentabilité par jour, prévisions de vente).
- Sois  professionnel ,direct, factuel et orienté vers des solutions concrètes pour chaque type de journée (creuse ou pleine).
- Organise ta réponse visuellement avec des titres clairs (###) et des puces (-).
- Approfondis tes solutions : explique concrètement comment le gérant peut adapter sa stratégie commerciale et opérationnelle selon le jour de la semaine.
"""

    # --- VARIABLE 2 : Content ---
    users_texte = """
Voici l'évolution du Chiffre d'Affaires (CA) jour par jour extraite de la caisse.

CONSIGNES DE TRAITEMENT :
- Attention : Si un jour affiche un CA de 0 ou extrêmement bas par rapport aux autres, considère qu'il s'agit d'un jour de fermeture ou d'un problème technique. Ne le traite pas comme un "Flop" commercial.

MISSION SPÉCIFIQUE :
1- Performance : Identifie clairement le jour le plus rentable (Pic) et le jour le moins rentable (Creux).
2- Constat : Détecte la tendance principale de la semaine (ex: démarrage lent, explosion le week-end).
3- Plan d'action Express : Suggère une promotion spécifique ou un événement pour booster le jour le plus faible, et donne un conseil sur la gestion du personnel (staffing) ou des stocks en fonction de cette tendance.

Données des ventes :
""" + s_resume

    return demande, users_texte


# ==========================================================
# 3. PaiementEtAnnulation
# ==========================================================
def paiement_et_annulation(commandes: list[Commande]) -> tuple[str, str]:
    """
    Équivalent PROCÉDURE PaiementEtAnnulation(Demande, UsersTexte)
    """
    tab_annulation: dict[str, dict] = {}

    def _init_si_absent(cle: str):
        if cle not in tab_annulation:
            tab_annulation[cle] = {"nom": cle, "Montant": 0.0, "Qt": 0}

    for commande in commandes:
        if commande.CommandeAnnule:
            for reg in commande.tabReg:
                cle = f"Annulation: {reg.Reglement}"
                _init_si_absent(cle)
                tab_annulation[cle]["nom"] = cle
                tab_annulation[cle]["Montant"] += reg.Montant
                tab_annulation[cle]["Qt"] += 1
        else:
            cle = "Pas annulation"
            _init_si_absent(cle)
            tab_annulation[cle]["nom"] = cle
            tab_annulation[cle]["Montant"] += commande.MontantTotal
            tab_annulation[cle]["Qt"] += 1

    s_resume = json.dumps(tab_annulation, ensure_ascii=False)

    demande = """
Tu es un auditeur financier et expert en gestion de caisse spécialisé dans la restauration. Ton rôle est d'analyser la santé financière d'un établissement, de détecter les anomalies potentielles (fraudes, erreurs) et d'optimiser les flux d'encaissement.
RÈGLES DE RÉDACTION STRICTES :
- Garde un ton strictement professionnel, impartial et rigoureux. Ne joue pas de rôle théâtral et évite toute familiarité ou jugement de valeur subjectif.
- Parle "sécurité financière", "audit" et "gestion des risques" (démarque inconnue, procédures de contrôle, traçabilité des annulations).
- Sois professionnel, direct, factuel et précis dans tes recommandations.
- Organise ta réponse de manière très visuelle avec des titres clairs (###) et des puces (-).
- Approfondis tes solutions : explique concrètement comment sécuriser les procédures d'encaissement et limiter les pertes financières.
"""

    users_texte = """
Voici le résumé des méthodes de paiement utilisées et le montant total des commandes annulées (pertes potentielles) extraits de la caisse.

CONSIGNES DE TRAITEMENT :
- Garde à l'esprit que dans la restauration rapide, un taux d'annulation élevé est un signal d'alerte rouge (besoin de formation du personnel ou risque de vol/fraude).
- L'espèce (Cash) ralentit la file d'attente et augmente le risque d'erreur, tandis que la Carte Bancaire ou le Sans Contact accélèrent le service.

MISSION SPÉCIFIQUE :
1- Diagnostic des Annulations : Le montant des annulations est-il alarmant ? Est-ce le signe d'erreurs de saisie fréquentes ou un risque de vol ? Que doit vérifier le gérant en priorité sur son logiciel ?
2- Optimisation des Paiements : Analyse la répartition des paiements. Faut-il encourager un moyen spécifique pour gagner du temps aux heures de pointe (ex: file dédiée Carte Bancaire, orientation vers les bornes) ?
3- Plan d'action Sécurité : Donne 2 recommandations pratiques et immédiates pour sécuriser l'argent et réduire les annulations frauduleuses.

Données financières :
""" + s_resume

    return demande, users_texte


# ==========================================================
# 4. HeureDePointe
# ==========================================================
def heure_de_pointe(commandes: list[Commande]) -> tuple[str, str]:
    """
    Équivalent PROCÉDURE HeureDePointe(Demande, UsersTexte)
    """
    tab_heures: dict[str, dict] = {}

    for commande in commandes:
        s_heure = commande.DateHeure[8:10] + "h"

        if s_heure not in tab_heures:
            tab_heures[s_heure] = {"nom": s_heure, "Montant": 0.0, "Qt": 0}

        tab_heures[s_heure]["nom"] = s_heure
        tab_heures[s_heure]["Montant"] += commande.MontantTotal
        tab_heures[s_heure]["Qt"] += 1

    s_resume = ""
    for elemnt in tab_heures.values():
        s_resume += f"{elemnt['nom']}->Qt={elemnt['Qt']},CA-->{elemnt['Montant']}\n"

    demande = """
Tu es un consultant expert en gestion opérationnelle de restaurant et en rentabilité. Ton objectif est d'analyser le flux de revenus par heure pour aider le gérant à optimiser le planning de son personnel et ses actions marketing.
RÈGLES DE RÉDACTION STRICTES :
- Garde un ton strictement professionnel, analytique et neutre. Ne joue pas de rôle théâtral et n'utilise JAMAIS d'expressions familières ou d'ordres infantilisants.
- Parle "business" et "terrain" (optimisation du planning, gestion du rush, rentabilité horaire, temps d'attente).
- Sois professionnel,  direct, factuel et évite tout jargon théorique inutile.
- Organise ta réponse de manière très visuelle avec des titres clairs (###) et des puces (-).
- Approfondis tes solutions : explique concrètement comment optimiser la mise en place en cuisine et le staffing en salle en fonction des pics et des creux.
"""

    users_texte = """
Voici le Chiffre d'Affaires (CA) réalisé par tranche horaire, extrait du logiciel de caisse.

CONSIGNES DE TRAITEMENT :
- Ne considère pas les heures avec un CA de 0 (ou quasi nul) comme des "heures creuses" à dynamiser, car cela correspond de toute évidence aux heures de fermeture du restaurant.
- Concentre-toi sur les moments de la journée où le restaurant est réellement ouvert mais où l'activité est faible.

MISSION SPÉCIFIQUE :
1- Diagnostic du Flux : Identifie clairement la période de Rush (le grand pic d'activité) et la vraie période Creuse (la baisse de régime pendant l'ouverture).
2- Organisation du Rush : Propose une stratégie concrète de gestion du personnel (staffing) et de préparation en cuisine (mise en place) pour anticiper ce pic, servir plus vite et éviter le chaos.
3- Boost des Heures Creuses : Donne une idée créative et ultra-pratique (ex: Happy Hour, menu goûter étudiant, promo ciblée sur les plateformes de livraison) pour attirer des clients pendant le moment le plus faible de la journée.

Chiffre d'Affaires par Heure :
""" + s_resume

    return demande, users_texte


# ==========================================================
# 5. CaneauxDeVente
# ==========================================================
def caneaux_de_vente(commandes: list[Commande]) -> tuple[str, str]:
    """
    Équivalent PROCÉDURE CaneauxDeVente(Demande, UsersTexte)
    """
    tab_mode_vente: dict[str, dict] = {}

    for commande in commandes:
        cle = commande.ModeDeVente

        if cle not in tab_mode_vente:
            tab_mode_vente[cle] = {"nom": cle, "Montant": 0.0, "Qt": 0}

        tab_mode_vente[cle]["nom"] = cle
        tab_mode_vente[cle]["Montant"] += commande.MontantTotal
        tab_mode_vente[cle]["Qt"] += 1

    s_resume = ""
    for elemnt in tab_mode_vente.values():
        s_resume += f"{elemnt['nom']}->Qt={elemnt['Qt']},CA-->{elemnt['Montant']}\n"

    demande = """
Tu es un consultant expert en gestion omnicanale de restaurant et en optimisation des flux opérationnels. Ton rôle est d'analyser les canaux de vente pour fluidifier le service, éviter les encombrements et optimiser l'agencement du local.
RÈGLES DE RÉDACTION STRICTES :
- Garde un ton strictement professionnel, neutre et factuel. Ne joue pas de rôle théâtral et n'utilise aucune expression familière ou tutoiement.
- Parle "business" et "terrain" (rotation des tables, gestion des flux livreurs, zone de retrait, expérience client).
- Sois professionnel,  direct et orienté vers des solutions logistiques concrètes.
- Organise ta réponse visuellement avec des titres clairs (###) et des puces (-).
- Approfondis tes solutions : explique concrètement comment réorganiser l'espace ou le service pour séparer les flux sans perturber l'activité.
"""

    users_texte = """
Voici la répartition du Chiffre d'Affaires par Mode de Vente (Sur place, à emporter, Livraison, Borne, etc.) extraite du logiciel de caisse.

CONSIGNES DE TRAITEMENT :
- Prends en compte que le "Sur place" exige une rotation rapide des tables et de la propreté, tandis que le "à emporter" et la "Livraison" exigent une rapidité d'emballage et une zone de retrait claire pour éviter de bloquer la caisse principale.

MISSION SPÉCIFIQUE :
1- Analyse Comportementale : Identifie la tendance principale. Les clients sont-ils plutôt pressés (Takeaway/Livraison) ou cherchent-ils l'expérience en salle ?
2- Optimisation de l'Espace (Le Flux) : Donne EXACTEMENT 2 conseils concrets d'aménagement physique pour éviter la confusion (ex: créer un comptoir de retrait express dédié aux livreurs, ajouter une signalétique au sol, installer des bornes de commande).
3- Stratégie de Canal : Suggère une action simple pour booster le canal le plus rentable ou désengorger le canal le plus saturé (ex: promotion exclusive "Click & Collect" pour réduire la file d'attente).

Données des modes de vente :
""" + s_resume

    return demande, users_texte


# ==========================================================
# 6. OrigineCommande
# ==========================================================
def origine_commande(commandes: list[Commande]) -> tuple[str, str]:
    """
    Équivalent PROCÉDURE OrigineCommande(Demande, UsersTexte)

    NOTE : dans le code WLangage d'origine, .nom est assigné à ModeDeVente
    (et non Origine) — probable bug de copier-coller dans le script d'origine.
    Reproduit à l'identique pour garder EXACTEMENT la même logique/sortie.
    """
    tab_origine: dict[str, dict] = {}

    for commande in commandes:
        cle = commande.Origine

        if cle not in tab_origine:
            tab_origine[cle] = {"nom": commande.ModeDeVente, "Montant": 0.0, "Qt": 0}

        tab_origine[cle]["nom"] = commande.ModeDeVente
        tab_origine[cle]["Montant"] += commande.MontantTotal
        tab_origine[cle]["Qt"] += 1

    s_resume = ""
    for elemnt in tab_origine.values():
        s_resume += f"{elemnt['nom']}->Qt={elemnt['Qt']},CA-->{elemnt['Montant']}\n"

    demande = """
Tu es un consultant expert en digitalisation de restaurants et en optimisation des ventes. Ton rôle est d'analyser l'origine des commandes (Borne tactile vs Caisse classique) pour améliorer la productivité du personnel et l'expérience client.
RÈGLES DE RÉDACTION STRICTES :
- Garde un ton strictement professionnel, objectif et analytique. Ne joue pas de rôle théâtral et évite toute familiarité ou enthousiasme excessif.
- Parle "business" (ticket moyen, productivité, fluidité du flux, taux d'adoption digital).
- Sois professionnel,  direct, factuel et sans jargon théorique inutile.
- Organise ta réponse visuellement avec des titres clairs (###) et des puces (-).
- Approfondis tes solutions : explique concrètement comment agir sur le terrain pour optimiser l'usage des bornes et fluidifier le service en caisse.
"""

    users_texte = """
Voici la répartition du Chiffre d'Affaires par Origine de commande (Borne tactile vs Caisse principale) extraite du logiciel de caisse.

CONSIGNES DE TRAITEMENT :
- Garde à l'esprit que la Borne augmente généralement le ticket moyen (grâce aux photos et aux suggestions automatiques) et désengorge la file d'attente.
- La Caisse reste indispensable pour les paiements en espèces et le contact humain.

MISSION SPÉCIFIQUE :
1- Analyse Comportementale : Identifie la tendance principale. Les clients préfèrent-ils l'autonomie du digital (Borne) ou le contact humain (Caisse) ?
2- Impact sur le Service : Fais le lien entre ces origines de commande et la fluidité du restaurant aux heures de pointe.
3- Plan d'action Stratégique : Donne EXACTEMENT 2 conseils concrets et rentables (ex: investir dans une nouvelle borne, placer un employé 'Groom' pour guider les clients vers les bornes, optimiser les suggestions automatiques sur l'écran).

Données des origines de commande :
""" + s_resume

    return demande, users_texte


# ==========================================================
# 7. PerfermonceParUtilisateur
# ==========================================================
def perfermonce_par_utilisateur(commandes: list[Commande]) -> tuple[str, str]:
    """
    Équivalent PROCÉDURE PerfermonceParUtilisateur(Demande, UsersTexte)
    """
    tab_utilisateur: dict[str, dict] = {}

    for commande in commandes:
        cle = commande.Utilisateur

        if cle not in tab_utilisateur:
            tab_utilisateur[cle] = {"nom": cle, "Montant": 0.0, "Qt": 0}

        tab_utilisateur[cle]["nom"] = cle
        tab_utilisateur[cle]["Montant"] += commande.MontantTotal
        tab_utilisateur[cle]["Qt"] += 1

    s_resume = ""
    for elemnt in tab_utilisateur.values():
        s_resume += f"{elemnt['nom']}->Qt={elemnt['Qt']},CA-->{elemnt['Montant']}\n"

    demande = """
Tu es un consultant expert en management d'équipe et en techniques de vente en restauration. Ton rôle est d'analyser les performances des caissiers/vendeurs pour booster le chiffre d'affaires et motiver l'équipe.
RÈGLES DE RÉDACTION STRICTES :
- Garde un ton strictement professionnel, neutre et bienveillant. Ne joue pas de rôle théâtral (pas d'attitude de "coach sportif" ou de gourou, pas de tutoiement familier).
- Parle "management" et "rentabilité" (upselling, ticket moyen, coaching, motivation).
- Sois professionnel, direct, constructif et factuel (ne sois jamais punitif, ni familier).
- Organise ta réponse visuellement avec des titres clairs (###) et des puces (-).
- Propose des solutions humaines et commerciales faciles à mettre en place par le gérant.
"""

    users_texte = """
Voici les performances de vente réparties par utilisateur/employé (caissiers), extraites du logiciel de caisse.

CONSIGNES DE TRAITEMENT :
- Garde à l'esprit que le but est d'encourager la technique de vente ("Upselling" : proposer des frites, des desserts, des grandes tailles).
- Ne propose pas de licencier ou de punir, mais plutôt de former ou de récompenser.

MISSION SPÉCIFIQUE :
1- Podium des Ventes : Identifie le profil "Star" (le meilleur vendeur) et le profil "à coacher" (celui qui génère le moins de chiffre).
2- Analyse Commerciale : Que traduisent ces chiffres ? Y a-t-il un manque de proposition de suppléments chez le vendeur le plus faible ?
3- Plan d'action Management : Donne EXACTEMENT 2 recommandations pratiques au gérant (ex: créer un challenge "Meilleur Vendeur du mois" avec une prime, mettre le top vendeur en binôme pour former les nouveaux).

Données par Employé :
""" + s_resume

    return demande, users_texte


# ==========================================================
# 8. AnalyseParCaisse
# ==========================================================
def analyse_par_caisse(commandes: list[Commande]) -> tuple[str, str]:
    """
    Équivalent PROCÉDURE AnalyseParCaisse(Demande, UsersTexte)
    """
    tab_caisse: dict[str, dict] = {}

    for commande in commandes:
        cle = f"Caisse {commande.caisse}"

        if cle not in tab_caisse:
            tab_caisse[cle] = {"nom": cle, "Montant": 0.0, "Qt": 0}

        tab_caisse[cle]["nom"] = cle
        tab_caisse[cle]["Montant"] += commande.MontantTotal
        tab_caisse[cle]["Qt"] += 1

    s_resume = ""
    for elemnt in tab_caisse.values():
        s_resume += f"{elemnt['nom']}->Qt={elemnt['Qt']},CA-->{elemnt['Montant']}\n"

    demande = """
Tu es un consultant expert en aménagement d'espace et en optimisation du flux client. Ton rôle est d'analyser les performances par point d'encaissement (caisses physiques) pour désengorger le restaurant et optimiser l'utilisation du matériel.
RÈGLES DE RÉDACTION STRICTES :
- Garde un ton strictement professionnel, neutre et objectif. Ne joue pas de rôle théâtral et n'utilise JAMAIS d'expressions familières ou clichées.
- Parle "business", "flux" et "logistique" (goulot d'étranglement, file d'attente, usure machine).
- Sois professionnel,  direct, factuel et sans jargon théorique.
- Organise ta réponse avec des titres clairs (###) et des puces (-).
- Approfondis tes solutions avec des actions physiques et concrètes sur le terrain.
"""

    users_texte = """
Voici la répartition du Chiffre d'Affaires par matériel d'encaissement (ex: Caisse Principale, Caisse 2, Caisse Drive, etc.) extraite du logiciel.

CONSIGNES DE TRAITEMENT :
- Un fort déséquilibre entre les caisses indique un problème de gestion de la file d'attente ou un mauvais emplacement.
- La caisse avec le plus de transactions est le "goulot d'étranglement" de l'équipe.

MISSION SPÉCIFIQUE :
1- Diagnostic Logistique : Identifie la caisse qui subit le plus de pression (risque de panne/stress) et celle qui est sous-exploitée.
2- Analyse de l'Aménagement : Pourquoi ce déséquilibre ? Est-ce un problème de visibilité (caisse cachée) ou de répartition du staff ?
3- Plan d'action Opérationnel : Propose EXACTEMENT 2 solutions logistiques pour équilibrer le flux (ex: déplacer une caisse, imposer l'ouverture de la Caisse 2 aux heures de pointe, changer la signalétique).

Données par Caisse :
""" + s_resume

    return demande, users_texte


# ==========================================================
# 9. PanierAssocie
# ==========================================================
def panier_associe(commandes: list[Commande]) -> tuple[str, str]:
    """
    Équivalent PROCÉDURE PanierAssocie(Demande, UsersTexte)
    """
    tab_comptage_paires: dict[str, int] = {}
    s_resume = "[Combinaisons de produits dans le même ticket]\n"

    for commande in commandes:
        n_nb_articles = len(commande.Ligven)
        if n_nb_articles > 1:
            for i in range(n_nb_articles - 1):
                for j in range(i + 1, n_nb_articles):
                    s_produit1 = commande.Ligven[i].Nom
                    s_produit2 = commande.Ligven[j].Nom
                    if s_produit1 < s_produit2:
                        s_cle_paire = f"{s_produit1} + {s_produit2}"
                    else:
                        s_cle_paire = f"{s_produit2} + {s_produit1}"
                    tab_comptage_paires[s_cle_paire] = tab_comptage_paires.get(s_cle_paire, 0) + 1

    for s_nom_paire, n_nombre_occurrences in tab_comptage_paires.items():
        if n_nombre_occurrences >= 5:
            s_resume += f"- {s_nom_paire} : {n_nombre_occurrences} fois\n"

    # NOTE : ce calcul existe dans le WLangage d'origine mais n'est en réalité
    # jamais utilisé dans sResume/Demande/UsersTexte (code mort). Reproduit
    # tel quel pour garder exactement la même logique.
    tab_liste_produit: dict[str, int] = {}
    for commande in commandes:
        for ligne in commande.Ligven:
            tab_liste_produit[ligne.Nom] = tab_liste_produit.get(ligne.Nom, 0) + ligne.Qte

    demande = """
Tu es un consultant expert en "Menu Engineering" et techniques d'Upselling en restauration. Ton rôle est d'analyser les habitudes d'achat croisées pour aider le gérant à créer des Menus rentables et augmenter son Ticket Moyen.
RÈGLES DE RÉDACTION STRICTES :
- Garde un ton strictement professionnel, objectif et respectueux. Ne joue pas de rôle théâtral et n'utilise JAMAIS de phrases familières, de tutoiement agressif ou d'expressions clichées (pas de "écoute bien", "C'est parti", etc.).
- Parle "business" et "rentabilité" (Ticket Moyen, Combo, Marge, Upselling en caisse).
- Sois professionnel, direct et orienté action, en te basant uniquement sur les données.
- Organise ta réponse visuellement avec des titres (###) et des puces (-).
- Approfondis tes solutions : explique concrètement comment mettre en place ces combos sur le point de vente et donne des exemples de phrases courtoises à utiliser par le caissier.
"""

    users_texte = """
Voici les combinaisons de produits les plus fréquemment achetées ensemble dans le même ticket de caisse (Paniers associés).

CONSIGNES DE TRAITEMENT :
- Ces données représentent des "Duos" de produits naturellement choisis par les clients sans qu'ils y soient forcément incités.
- Ton but est de conseiller le gérant pour transformer ces habitudes spontanées en offres commerciales structurées et rentables.

MISSION SPÉCIFIQUE :
1- Les Couples Gagnants : Identifie les 2 ou 3 associations de produits les plus fortes (les stars du cross-selling).
2- Création d'Offres : Propose la création d'offres "Combo" ou de "Menus" officiels basés sur ces associations. Donne des idées d'approche commerciale (ex: faire une petite réduction sur l'achat groupé pour encourager le volume).
3- Stratégie d'Upselling au comptoir : Donne 2 phrases d'accroche pratiques que le caissier doit dire pour vendre ces combos facilement (ex: "Pour 1 dinar de plus, prenez la boisson avec !").

Données des associations de produits :
""" + s_resume

    return demande, users_texte


# ==========================================================
# 10. PrevisionDesStocks
# ==========================================================
def prevision_des_stocks(commandes: list[Commande]) -> tuple[str, str]:
    """
    Équivalent PROCÉDURE PrevisionDesStocks(Demande, UsersTexte)
    """
    tab_date_produit: dict[str, dict] = {}

    for commande in commandes:
        for ligne in commande.Ligven:
            jours_ut = commande.DateHeure[:8]
            cle = f"{jours_ut}__{ligne.Nom}"

            if cle not in tab_date_produit:
                tab_date_produit[cle] = {"nom": cle, "Montant": 0.0, "Qt": 0}

            tab_date_produit[cle]["nom"] = cle
            tab_date_produit[cle]["Montant"] += ligne.Prix
            tab_date_produit[cle]["Qt"] += ligne.Qte

    s_resume = ""
    for elemnt in tab_date_produit.values():
        s_date_en_chaine, s_produit_enchaine = elemnt["nom"].split("__", 1)
        s_resume += f"{s_date_en_chaine},{s_produit_enchaine}:->Qt={elemnt['Qt']},CA-->{elemnt['Montant']}\n"

    demande = """
Tu es un consultant expert en gestion des stocks de restauration. Ton rôle est d'analyser l'historique des ventes par date pour aider le gérant à anticiper la "mise en place" en cuisine.
RÈGLES DE RÉDACTION STRICTES :
- Garde un ton neutre, professionnel et très respectueux. Ne joue pas un rôle théâtral et n'utilise JAMAIS de phrases familières ou d'ordres (interdiction d'utiliser des expressions comme "écoute bien", "Au boulot", etc.).
- Parle le langage "business" et "cuisine" (mise en place, anticipation, pics, gaspillage).
- sois  professionnel et direct.
- Organise ta réponse avec des titres (###) et des puces (-).
- Tes conseils doivent être des recommandations objectives, pas des ordres.
"""

    users_texte = """
Voici l'historique détaillé des quantités vendues par produit et par date, extrait du logiciel de caisse.

CONSIGNES DE TRAITEMENT :
- Analyse l'évolution chronologique. Repère les modèles (patterns) : tendances des week-ends, pics de fin ou début de mois, etc.
- L'objectif est d'éviter la rupture de stock (qui frustre le client) tout en limitant la surproduction (qui finit à la poubelle).

MISSION SPÉCIFIQUE :
1- Analyse Chronologique : Identifie le rythme de vente des produits clés selon les dates exactes (ex: forte Demande sur un produit spécifique à certaines dates).
2- Plan de "Mise en place" : Donne des recommandations claires à l'équipe de cuisine sur ce qu'ils doivent préparer, couper ou décongeler en priorité pour les jours à venir.
3- Alerte Anti-Gaspillage : Identifie les produits dont les ventes sont instables ou très faibles, et donne un conseil strict sur leur gestion au quotidien pour éviter les pertes.

Données de ventes par date :
""" + s_resume

    return demande, users_texte