"""
Équivalent WLangage du bouton "btn_rapport" (le clic déclenche toute la
génération), exposé ici comme route Flask.

Routes principales :
    POST /generer-rapport
        -> body JSON optionnel {"categories": ["heures_pointe", "top_flop", ...]}
           (sous-ensemble des 10 analyses ; absent/vide = les 10)
        -> optionnel : fichier JSON envoyé en multipart (champ "fichier")
        -> sinon : charge selon DATA_SOURCE_TYPE (local ou URL, voir config.py)
    GET  /categories        -> liste des 10 catégories (pour les cases à cocher)
    GET  /rapports           -> liste des dates de rapports déjà générés
    GET  /rapports/<date>    -> contenu du rapport généré ce jour-là
    POST /rapport-pdf         -> convertit des sections déjà générées en PDF

Un job planifié (APScheduler) génère automatiquement le rapport complet
une fois par jour, sans action de l'utilisateur (voir _tache_quotidienne).
"""

import io
from pathlib import Path

from flask import Flask, jsonify, request, Response, render_template, send_file, session, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import DATA_SOURCE_TYPE, DATA_URL, HEURE_RAPPORT_QUOTIDIEN
from app.services.data_loader import charger_commandes_lbms
from app.services.rapport import generer_rapport_complet, liste_categories
from app.services.gemini_client import traceut, list_models, set_current_model, get_current_model
from app.auth import require_role, load_users, save_users, login_required, authenticate_user, hash_password
from app.services.pdf_export import generer_pdf
from app.services import historique
from app.db import get_parametre, set_parametre

app = Flask(__name__)
app.secret_key = "pos_reporting_dev_secret_key"

DEFAULT_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "Texte.json"
LBMS_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "lbms_exemple.json"


def _charger_commandes_par_defaut():

    if DATA_SOURCE_TYPE == "url":
        if not DATA_URL:
            raise ValueError("DATA_SOURCE_TYPE=url mais DATA_URL est vide (voir .env)")
        return charger_commandes_lbms(DATA_URL)
    return charger_commandes_lbms(LBMS_JSON_PATH)


@app.route("/", methods=["GET"])
def accueil():
    return render_template(
        "index.html",
        is_admin=session.get("role") == "admin",
        user=session.get("user_id"),
    )


@app.route("/login", methods=["GET", "POST"])
def connexion():
    erreur = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = authenticate_user(username, password)
        if user:
            session["user_id"] = username
            session["role"] = user.get("role", "user")
            if session.get("role") == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("accueil"))
        erreur = "Identifiants invalides."
    return render_template("login.html", erreur=erreur)


@app.route("/logout", methods=["GET"])
def deconnexion():
    session.clear()
    return redirect(url_for("connexion"))


@app.route("/admin", methods=["GET"])
@require_role("admin")
def admin_dashboard():
    users = load_users()
    rapport_dates = historique.lister_dates_disponibles()
    provider = get_parametre("ai_provider", "gemini")
    gemini_config = bool(get_parametre("gemini_api_key", ""))
    openai_config = bool(get_parametre("openai_api_key", ""))
    return render_template(
        "admin_dashboard.html",
        user=session.get("user_id"),
        is_admin=True,
        total_utilisateurs=len(users),
        utilisateurs_actifs=sum(1 for u in users if u.get("enabled", True)),
        total_rapports=len(rapport_dates),
        dernier_rapport=rapport_dates[0] if rapport_dates else "aucun",
        provider_actif=provider,
        gemini_config=gemini_config,
        openai_config=openai_config,
    )


@app.route("/historique", methods=["GET"])
def page_historique():
    return render_template("historique.html")


@app.route("/categories", methods=["GET"])
def categories():
    """Pour construire les cases à cocher côté front-end."""
    return jsonify({"categories": liste_categories()})


@app.route("/generer-rapport", methods=["POST"])
def generer_rapport():

    fmt = request.args.get("format", "json")  # "json" ou "html"

    payload = request.get_json(silent=True) or {}
    categories_demandees = payload.get("categories") or None

    # --- Chargement des commandes ---
    try:
        if "fichier" in request.files:
            fichier = request.files["fichier"]
            chemin_temp = Path("/tmp") / fichier.filename
            fichier.save(chemin_temp)
            commandes = charger_commandes_lbms(chemin_temp)
        else:
            commandes = _charger_commandes_par_defaut()
    except Exception as e:
        traceut(f"Erreur de chargement des commandes : {e}")
        return jsonify({"erreur": f"Impossible de charger les commandes : {e}"}), 400

    if not commandes:
        return jsonify({"erreur": "Aucune commande à analyser."}), 400

    # --- Génération du rapport (boucle principale, catégories filtrées ou non) ---
    try:
        sections = generer_rapport_complet(commandes, categories=categories_demandees)
    except Exception as e:
        traceut(f"Erreur pendant la génération du rapport : {e}")
        return jsonify({"erreur": f"Erreur pendant la génération du rapport : {e}"}), 500

    if fmt == "html":
        return _rendre_rapport_html(sections)

    return jsonify({
        "nombre_commandes_analysees": len(commandes),
        "sections": sections,
    })


@app.route("/rapports", methods=["GET"])
def rapports_disponibles():
    """Liste des dates pour lesquelles un rapport automatique existe déjà."""
    return jsonify({"dates": historique.lister_dates_disponibles()})


@app.route("/admin/users", methods=["GET"])
@require_role("admin")
def admin_list_users():
    users = load_users()
    # Ne pas exposer les mots de passe
    safe = [{k: v for k, v in u.items() if k != "password"} for u in users]
    return jsonify({"users": safe})


@app.route("/admin/users/<username>/role", methods=["POST"])
@require_role("admin")
def admin_change_role(username):
    payload = request.get_json(silent=True) or {}
    new_role = payload.get("role")
    if not new_role:
        return jsonify({"erreur": "role requis dans le body"}), 400
    users = load_users()
    for u in users:
        if u.get("username") == username:
            u["role"] = new_role
            save_users(users)
            return jsonify({"ok": True, "username": username, "role": new_role})
    return jsonify({"erreur": "utilisateur introuvable"}), 404


@app.route("/admin/users/<username>/enable", methods=["POST"])
@require_role("admin")
def admin_enable_user(username):
    payload = request.get_json(silent=True) or {}
    enabled = payload.get("enabled")
    if enabled is None:
        return jsonify({"erreur": "champ 'enabled' requis (true/false)"}), 400
    users = load_users()
    for u in users:
        if u.get("username") == username:
            u["enabled"] = bool(enabled)
            save_users(users)
            return jsonify({"ok": True, "username": username, "enabled": bool(enabled)})
    return jsonify({"erreur": "utilisateur introuvable"}), 404


@app.route("/admin/gemini/switch", methods=["POST"])
@require_role("admin")
def admin_switch_gemini():
    payload = request.get_json(silent=True) or {}
    model = payload.get("model")
    if not model:
        return jsonify({"erreur": "model requis dans le body"}), 400
    # Change le modèle courant (ou endpoint) utilisé par le client Gemini
    try:
        set_current_model(model)
    except Exception as e:
        return jsonify({"erreur": f"impossible de changer le modèle : {e}"}), 500
    return jsonify({"current_model": get_current_model(), "available": list_models()})


@app.route("/rapports/<date>", methods=["GET"])
def rapport_du_jour(date):
    """Contenu du rapport généré automatiquement à une date donnée (AAAA-MM-JJ)."""
    rapport = historique.charger_rapport(date)
    if rapport is None:
        return jsonify({"erreur": f"Aucun rapport trouvé pour le {date}."}), 404
    return jsonify(rapport)


@app.route("/rapports/comparaison", methods=["GET"])
@login_required
def comparaison_rapports():
    date1 = request.args.get("date1")
    date2 = request.args.get("date2")
    if not date1 or not date2:
        return jsonify({"erreur": "Fournis date1 et date2 en paramètres."}), 400
    resultat = historique.comparer_rapports(date1, date2)
    if resultat is None:
        return jsonify({"erreur": "Rapport introuvable pour une des deux dates."}), 404
    return jsonify(resultat)


def _rendre_rapport_html(sections: list[dict]) -> Response:
    """
    Équivalent visuel de AjouteeTexte(..., "Arial", Vrai, 14, chCentre) pour les
    titres et AjouteeTexte(..., "Arial", Faux, 10, chGauche) pour le contenu,
    + BT_IMPRIMER1 (rapport prêt à être imprimé/exporté).
    """
    blocs_html = []
    for section in sections:
        titre = section["titre"]
        contenu = section["contenu"].replace("\n", "<br>")
        blocs_html.append(
            f'<h2 style="font-family:Arial; text-align:center;">{titre}</h2>'
            f'<div style="font-family:Arial; font-size:10pt; text-align:left;">{contenu}</div>'
            f'<hr>'
        )

    html = f"""
    <html>
    <head><meta charset="utf-8"><title>Rapport Marketing</title></head>
    <body>
        {"".join(blocs_html)}
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


@app.route("/rapport-pdf", methods=["POST"])
def rapport_pdf():
    """
    Reçoit les sections déjà générées (renvoyées par /generer-rapport) et
    les convertit en PDF téléchargeable. Évite de relancer les analyses IA.
    """
    payload = request.get_json(silent=True) or {}
    sections = payload.get("sections")
    nombre_commandes = payload.get("nombre_commandes")

    if not sections:
        return jsonify({"erreur": "Aucune section fournie pour générer le PDF."}), 400

    try:
        pdf_bytes = generer_pdf(sections, nombre_commandes)
    except Exception as e:
        traceut(f"Erreur génération PDF : {e}")
        return jsonify({"erreur": f"Erreur génération PDF : {e}"}), 500

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="rapport_marketing.pdf",
    )


# ==========================================
# Génération automatique quotidienne (sans clic)
# ==========================================
def _tache_quotidienne():
    """Appelée une fois par jour par le planificateur : génère et sauvegarde
    le rapport complet (les 10 analyses), sans action de l'utilisateur."""
    try:
        commandes = _charger_commandes_par_defaut()
        sections = generer_rapport_complet(commandes)  # toutes les catégories
        historique.sauvegarder_rapport(sections, nombre_commandes=len(commandes))
        traceut("Rapport quotidien automatique généré avec succès.")
    except Exception as e:
        traceut(f"Échec de la génération quotidienne automatique : {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(_tache_quotidienne, "cron", hour=HEURE_RAPPORT_QUOTIDIEN, minute=0)
scheduler.start()


@app.route("/admin/utilisateurs", methods=["GET", "POST"])
@require_role("admin")
def admin_utilisateurs_page():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        role = request.form.get("role", "user")
        if username and password:
            users = load_users()
            if any(u.get("username") == username for u in users):
                return render_template("admin_utilisateurs.html", utilisateurs=_format_users(users), message="Cet identifiant existe déjà.")
            users.append({"username": username, "password": hash_password(password), "role": role, "enabled": True})
            save_users(users)
            return render_template("admin_utilisateurs.html", utilisateurs=_format_users(users), message="Utilisateur créé.")

    users = load_users()
    return render_template("admin_utilisateurs.html", utilisateurs=_format_users(users), message=None)


def _format_users(users: list[dict]) -> list[dict]:
    formatted = []
    for idx, user in enumerate(users):
        formatted.append({
            "id": user.get("username") or str(idx),
            "username": user.get("username"),
            "role": user.get("role", "user"),
            "actif": bool(user.get("enabled", True)),
        })
    return formatted


@app.route("/admin/utilisateurs/<username>/basculer", methods=["POST"])
@require_role("admin")
def admin_utilisateur_basculer(username):
    users = load_users()
    for user in users:
        if user.get("username") == username:
            user["enabled"] = not bool(user.get("enabled", True))
            save_users(users)
            return redirect(url_for("admin_utilisateurs_page"))
    return redirect(url_for("admin_utilisateurs_page"))


@app.route("/admin/utilisateurs/<username>/supprimer", methods=["POST"])
@require_role("admin")
def admin_utilisateur_supprimer(username):
    users = load_users()
    users = [u for u in users if u.get("username") != username]
    save_users(users)
    return redirect(url_for("admin_utilisateurs_page"))


@app.route("/admin/parametres", methods=["GET", "POST"])
@require_role("admin")
def admin_parametres_page():
    message = None
    if request.method == "POST":
        fournisseur = request.form.get("ai_provider", "gemini")
        gemini_key = request.form.get("gemini_api_key")
        openai_key = request.form.get("openai_api_key")
        if fournisseur in {"gemini", "openai"}:
            set_parametre("ai_provider", fournisseur)
        if gemini_key:
            set_parametre("gemini_api_key", gemini_key)
        if openai_key:
            set_parametre("openai_api_key", openai_key)
        message = "Paramètres enregistrés."

    provider = get_parametre("ai_provider", "gemini")
    gemini_key = get_parametre("gemini_api_key", "")
    openai_key = get_parametre("openai_api_key", "")
    return render_template(
        "admin_parametres.html",
        fournisseur_actif=provider,
        gemini_masquee="********" if gemini_key else "aucune",
        openai_masquee="********" if openai_key else "aucune",
        message=message,
    )


@app.route("/api/dashboard", methods=["GET"])
def dashboard_stats():
    dates = historique.lister_dates_disponibles()
    provider = get_parametre("ai_provider", "gemini")
    gemini_config = bool(get_parametre("gemini_api_key", ""))
    openai_config = bool(get_parametre("openai_api_key", ""))
    return jsonify({
        "status": "ok",
        "user": session.get("user_id"),
        "is_admin": session.get("role") == "admin",
        "provider_ia": provider,
        "ia_status": {
            "provider": provider,
            "gemini_configured": gemini_config,
            "openai_configured": openai_config,
            "ready": provider == "gemini" and gemini_config or provider == "openai" and openai_config,
        },
        "nombre_rapports": len(dates),
        "dernier_rapport": dates[0] if dates else None,
    })


@app.route("/api/ia/status", methods=["GET"])
def ia_status():
    provider = get_parametre("ai_provider", "gemini")
    return jsonify({
        "provider": provider,
        "gemini_configured": bool(get_parametre("gemini_api_key", "")),
        "openai_configured": bool(get_parametre("openai_api_key", "")),
        "ready": provider == "gemini" and bool(get_parametre("gemini_api_key", "")) or provider == "openai" and bool(get_parametre("openai_api_key", "")),
    })


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "pos_reporting",
        "timestamp": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "user": session.get("user_id"),
        "is_admin": session.get("role") == "admin",
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)