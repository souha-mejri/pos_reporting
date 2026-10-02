#!/bin/bash
set -e

echo "🚀 Déploiement de pos-reporting sur Kubernetes"
echo ""

# Variables à configurer
GITHUB_USER="${GITHUB_USER:-VOTRE_USER_GITHUB}"
GITHUB_TOKEN="${GITHUB_TOKEN:-VOTRE_TOKEN_GITHUB}"

echo "📦 1. Installation du contrôleur Ingress NGINX..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.2/deploy/static/provider/baremetal/deploy.yaml

echo "⏳ Attente que l'Ingress Controller soit prêt..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

echo ""
echo "📋 2. Création du namespace..."
kubectl apply -f namespace.yaml

echo ""
echo "🔐 3. Création des secrets..."

# Secret pour GHCR
if [ -z "$GITHUB_TOKEN" ] || [ "$GITHUB_TOKEN" = "VOTRE_TOKEN_GITHUB" ]; then
  echo "⚠️  GITHUB_TOKEN non défini. Création du secret manuellement :"
  echo "kubectl create secret docker-registry ghcr-secret \\"
  echo "  --docker-server=ghcr.io \\"
  echo "  --docker-username=VOTRE_USER \\"
  echo "  --docker-password=VOTRE_TOKEN \\"
  echo "  -n pos-reporting"
else
  kubectl create secret docker-registry ghcr-secret \
    --docker-server=ghcr.io \
    --docker-username="$GITHUB_USER" \
    --docker-password="$GITHUB_TOKEN" \
    -n pos-reporting --dry-run=client -o yaml | kubectl apply -f -
  echo "✅ Secret ghcr-secret créé"
fi

# Secret pour l'app (.env)
if [ -f "../.env" ]; then
  kubectl create secret generic app-env \
    --from-env-file=../.env \
    -n pos-reporting --dry-run=client -o yaml | kubectl apply -f -
  echo "✅ Secret app-env créé depuis ../.env"
else
  echo "⚠️  Fichier ../.env non trouvé. Crée le secret manuellement :"
  echo "kubectl create secret generic app-env --from-env-file=.env -n pos-reporting"
fi

echo ""
echo "💾 4. Création du volume persistant..."
kubectl apply -f pvc.yaml

echo ""
echo "🚢 5. Déploiement de l'application..."
kubectl apply -f deployment.yaml

echo ""
echo "🌐 6. Création du Service et de l'Ingress..."
kubectl apply -f service-ingress.yaml

echo ""
echo "⏳ Attente que le pod soit prêt..."
kubectl wait --namespace pos-reporting \
  --for=condition=ready pod \
  --selector=app=pos-reporting \
  --timeout=120s

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "📊 État du déploiement :"
kubectl get pods -n pos-reporting
echo ""
kubectl get svc -n pos-reporting
echo ""
kubectl get ingress -n pos-reporting

echo ""
echo "🔍 Pour voir les logs :"
echo "kubectl logs -n pos-reporting -l app=pos-reporting -f"

echo ""
echo "🌍 NodePort de l'Ingress Controller :"
kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}'
echo ""
echo ""
echo "📝 Ajoute à C:\\Windows\\System32\\drivers\\etc\\hosts (en admin) :"
echo "192.168.158.204   pos-reporting.local"
echo ""
echo "🌐 Puis accède à : http://pos-reporting.local:NODEPORT"
