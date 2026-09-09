
# Image légère avec Python déjà installé
FROM python:3.12-slim
 
WORKDIR /app
 
# Installer les dépendances d'abord (mise en cache Docker : si le code change
# mais pas requirements.txt, cette étape n'est pas refaite -> builds plus rapides)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# Copier le reste du code
COPY . .
 
# Le port que l'app écoute à l'intérieur du conteneur
EXPOSE 5000
 
# Gunicorn = serveur de production (remplace "flask run")
# --workers 1 : IMPORTANT, un seul worker. Le planificateur (rapport quotidien
# automatique) tourne dans le process de l'app ; avec plusieurs workers, la
# tâche serait exécutée en double (voire plus) chaque jour.
# --timeout 600 : générer les 10 catégories avec cascade de secours entre
# ~19 modèles peut prendre plusieurs minutes dans le pire des cas ; 120s
# était trop court et provoquait un WORKER TIMEOUT (requête tuée en plein
# appel IA, avant même d'atteindre notre gestion d'erreur applicative).
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "600", "app.main:app"]