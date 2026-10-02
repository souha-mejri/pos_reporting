#!/bin/bash
# Script pour configurer HTTPS avec cert-manager

set -e

echo "🔒 Configuration HTTPS pour pos-reporting"
echo ""

# 1. Installer cert-manager
echo "📦 Installation de cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

echo "⏳ Attente que cert-manager soit prêt..."
kubectl wait --for=condition=Available --timeout=300s deployment/cert-manager -n cert-manager
kubectl wait --for=condition=Available --timeout=300s deployment/cert-manager-webhook -n cert-manager

echo "✅ cert-manager installé"
echo ""

# 2. Créer un ClusterIssuer pour Let's Encrypt (staging d'abord pour tester)
echo "📝 Création du ClusterIssuer Let's Encrypt..."
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: ton-email@example.com  # ⚠️ Change moi !
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
      - http01:
          ingress:
            class: nginx
EOF

echo "✅ ClusterIssuer créé"
echo ""

# 3. Mettre à jour l'Ingress pour utiliser TLS
echo "🔧 Mise à jour de l'Ingress..."
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pos-reporting
  namespace: pos-reporting
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-staging"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - pos-reporting.local
      secretName: pos-reporting-tls
  rules:
    - host: pos-reporting.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: pos-reporting
                port:
                  number: 80
EOF

echo "✅ Ingress mis à jour"
echo ""

# 4. Vérifier le certificat
echo "🔍 Vérification du certificat..."
sleep 5
kubectl get certificate -n pos-reporting

echo ""
echo "✅ Configuration HTTPS terminée !"
echo ""
echo "📝 Prochaines étapes:"
echo "  1. Vérifie que le certificat est prêt:"
echo "     kubectl describe certificate pos-reporting-tls -n pos-reporting"
echo ""
echo "  2. Une fois testé, passe en production:"
echo "     - Change 'letsencrypt-staging' en 'letsencrypt-prod'"
echo "     - Change le server en https://acme-v02.api.letsencrypt.org/directory"
echo ""
echo "  3. Accède à l'app en HTTPS:"
echo "     https://pos-reporting.local:NODEPORT"
