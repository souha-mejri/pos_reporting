# 🚀 Déploiement Kubernetes - RestoReport

## 📋 Prérequis

- Cluster Kubernetes fonctionnel (1 master + 2 workers minimum)
- kubectl configuré et connecté au cluster
- Image Docker publiée sur GHCR : `ghcr.io/VOTRE_USER/pos-reporting:latest`
- Token GitHub avec droit `read:packages`

## 🎯 Architecture

```
┌─────────────────────────────────────────┐
│         Ingress Controller              │
│    (NGINX - NodePort 30000-32767)       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Service pos-reporting           │
│            (ClusterIP:80)               │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Deployment pos-reporting           │
│         (1 replica - Flask)             │
│                                         │
│  Volume: /app/data (SQLite + logs)     │
└─────────────────────────────────────────┘
```

## 🚀 Déploiement automatique

### Méthode 1 : Script shell (recommandé)

1. **Sur Windows, transfère les fichiers** :
```powershell
# Depuis le dossier kubernetes/
scp -r . master@192.168.158.206:~/kubernetes/
```

2. **Sur le master, exécute le script** :
```bash
cd ~/kubernetes
chmod +x deploy.sh

# Configure tes identifiants GitHub
export GITHUB_USER="ton_username"
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"

# Lance le déploiement
./deploy.sh
```

### Méthode 2 : Déploiement manuel

```bash
# 1. Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.2/deploy/static/provider/baremetal/deploy.yaml

# 2. Namespace
kubectl apply -f namespace.yaml

# 3. Secrets
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=TON_USER \
  --docker-password=TON_TOKEN \
  -n pos-reporting

kubectl create secret generic app-env \
  --from-env-file=../.env \
  -n pos-reporting

# 4. Volume
kubectl apply -f pvc.yaml

# 5. Application
kubectl apply -f deployment.yaml

# 6. Service et Ingress
kubectl apply -f service-ingress.yaml
```

## 🔍 Vérification

```bash
# État des pods
kubectl get pods -n pos-reporting

# Logs de l'application
kubectl logs -n pos-reporting -l app=pos-reporting -f

# Services
kubectl get svc -n pos-reporting
kubectl get svc -n ingress-nginx

# Ingress
kubectl get ingress -n pos-reporting
```

## 🌐 Accès depuis Windows

1. **Récupère le NodePort** :
```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
# Note le port à côté de 80:XXXXX/TCP (ex: 30080)
```

2. **Ajoute à `C:\Windows\System32\drivers\etc\hosts`** (en Administrateur) :
```
192.168.158.204   pos-reporting.local
```

3. **Ouvre ton navigateur** :
```
http://pos-reporting.local:30080
```

## 🔄 Mise à jour de l'application

```bash
# Forcer le redémarrage avec la dernière image
kubectl rollout restart deployment/pos-reporting -n pos-reporting

# Suivre le rollout
kubectl rollout status deployment/pos-reporting -n pos-reporting
```

## 🐛 Dépannage

### Le pod ne démarre pas
```bash
# Voir les événements
kubectl describe pod -n pos-reporting -l app=pos-reporting

# Logs détaillés
kubectl logs -n pos-reporting -l app=pos-reporting --previous
```

### Problème d'image pull
```bash
# Vérifier le secret
kubectl get secret ghcr-secret -n pos-reporting -o yaml

# Recréer le secret
kubectl delete secret ghcr-secret -n pos-reporting
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=TON_USER \
  --docker-password=TON_TOKEN \
  -n pos-reporting
```

### L'Ingress ne fonctionne pas
```bash
# Vérifier l'Ingress Controller
kubectl get pods -n ingress-nginx

# Tester directement le Service
kubectl port-forward -n pos-reporting svc/pos-reporting 8080:80
# Puis ouvre http://localhost:8080
```

## ⚠️ Important

### Pourquoi replicas: 1 ?

L'application utilise **APScheduler** pour les tâches planifiées (rapport quotidien). Avec plusieurs replicas :
- Chaque pod aurait son propre scheduler
- Le rapport serait généré N fois (N = nombre de replicas)

**Solutions futures** :
1. Externaliser le scheduler dans un CronJob Kubernetes séparé
2. Utiliser un mécanisme de lock distribué (Redis, Consul)
3. Utiliser Celery Beat avec un seul worker

### Volume persistant

Le PVC utilise `ReadWriteOnce` - **un seul pod peut y accéder**. Avec plusieurs replicas, ils ne pourraient pas tous monter le même volume. Pour du multi-replica, il faudrait :
- Migrer vers PostgreSQL/MySQL (pas SQLite)
- Utiliser un stockage partagé (NFS, CephFS)

## 📊 Monitoring

```bash
# Ressources utilisées
kubectl top pod -n pos-reporting

# Événements récents
kubectl get events -n pos-reporting --sort-by='.lastTimestamp'

# Décrire le déploiement
kubectl describe deployment pos-reporting -n pos-reporting
```

## 🧹 Nettoyage

```bash
# Supprimer l'application
kubectl delete namespace pos-reporting

# Supprimer l'Ingress Controller
kubectl delete namespace ingress-nginx
```
