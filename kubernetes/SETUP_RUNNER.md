# Configuration du GitHub Actions Runner

Ce guide explique comment configurer un runner self-hosted pour le déploiement automatique sur Kubernetes.

## Prérequis

- ✅ Cluster Kubernetes opérationnel (3 VMs allumées)
- ✅ `kubectl` configuré et fonctionnel
- ✅ Accès administrateur au repository GitHub

---

## Option 1 : Runner sur VM directement (RECOMMANDÉ)

### Étape 1 : Obtenir le token GitHub

1. Allez sur : `https://github.com/souha-mejri/pos_reporting/settings/actions/runners/new`
2. Choisissez **Linux** et **x64**
3. **COPIEZ** la commande `./config.sh` qui contient le token

### Étape 2 : Installer sur k8s-master

Connectez-vous en SSH à `k8s-master` :

```bash
# Créer le dossier du runner
mkdir -p ~/actions-runner && cd ~/actions-runner

# Télécharger le runner
curl -o actions-runner-linux-x64-2.319.1.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.319.1/actions-runner-linux-x64-2.319.1.tar.gz

# Extraire
tar xzf ./actions-runner-linux-x64-2.319.1.tar.gz

# Configurer (REMPLACEZ par la commande copiée à l'étape 1)
./config.sh --url https://github.com/souha-mejri/pos_reporting --token VOTRE_TOKEN_ICI

# Répondre aux questions :
# - Enter the name of the runner group: [Entrée] (default)
# - Enter the name of runner: k8s-runner
# - Enter any additional labels: [Entrée]
# - Enter name of work folder: [Entrée] (_work)
```

### Étape 3 : Installer comme service système

```bash
# Installer le service
sudo ./svc.sh install

# Démarrer le service
sudo ./svc.sh start

# Vérifier le statut
sudo ./svc.sh status
```

### Étape 4 : Vérifier sur GitHub

Retournez sur `https://github.com/souha-mejri/pos_reporting/settings/actions/runners`

Vous devriez voir :
- ✅ **k8s-runner** avec le statut **Idle** (vert)

---

## Option 2 : Runner dans un pod Kubernetes (AVANCÉ)

### Étape 1 : Obtenir un Personal Access Token

1. Allez sur : `https://github.com/settings/tokens/new`
2. Nom : `runner-token-pos-reporting`
3. Cochez les permissions :
   - ✅ `repo` (Full control)
   - ✅ `workflow`
   - ✅ `admin:org` > `read:org`
4. Cliquez sur **Generate token**
5. **COPIEZ** le token (il commence par `ghp_`)

### Étape 2 : Modifier le fichier de configuration

Éditez `kubernetes/github-runner.yaml` et remplacez `VOTRE_TOKEN_ICI` par le token copié.

### Étape 3 : Déployer le runner

```bash
# Appliquer la configuration
kubectl apply -f kubernetes/github-runner.yaml

# Vérifier le pod
kubectl get pods -n github-runner

# Voir les logs
kubectl logs -n github-runner -l app=github-runner -f
```

### Étape 4 : Vérifier sur GitHub

Le runner devrait apparaître sur :
`https://github.com/souha-mejri/pos_reporting/settings/actions/runners`

---

## Tester le runner

### 1. Pusher un commit

```bash
git add .
git commit -m "test: trigger CI/CD with self-hosted runner"
git push
```

### 2. Vérifier le workflow

Allez sur : `https://github.com/souha-mejri/pos_reporting/actions`

Le workflow devrait :
- ✅ Passer les tests sur `ubuntu-latest`
- ✅ Builder l'image Docker
- ✅ Se connecter au runner `self-hosted`
- ✅ Déployer sur Kubernetes

### 3. Vérifier le déploiement

```bash
# Sur k8s-master
kubectl get pods -n pos-reporting -o wide

# Vérifier les logs
kubectl logs -n pos-reporting -l app=pos-reporting --tail=50
```

---

## Dépannage

### Le runner n'apparaît pas sur GitHub

```bash
# Option 1 (VM)
sudo ./svc.sh status
sudo ./svc.sh start

# Option 2 (Pod)
kubectl logs -n github-runner -l app=github-runner
kubectl describe pod -n github-runner -l app=github-runner
```

### Le workflow reste bloqué sur "Waiting for runner"

1. Vérifiez que le runner est **Idle** (vert) sur GitHub
2. Vérifiez que le label correspond : `self-hosted` dans le workflow
3. Redémarrez le runner :
   ```bash
   # VM
   sudo ./svc.sh restart
   
   # Pod
   kubectl rollout restart deployment/github-runner -n github-runner
   ```

### Le déploiement échoue sur "kubectl command not found"

Le runner doit avoir accès à `kubectl`. Sur la VM :

```bash
# Vérifier kubectl
kubectl version --client

# Si manquant, installer
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Configurer l'accès au cluster
mkdir -p ~/.kube
sudo cp /etc/kubernetes/admin.conf ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config
```

---

## Arrêter/Désactiver le runner

### VM
```bash
cd ~/actions-runner
sudo ./svc.sh stop
sudo ./svc.sh uninstall
```

### Pod
```bash
kubectl delete -f kubernetes/github-runner.yaml
```

---

## Sécurité

⚠️ **Important** : Le runner a accès complet à votre cluster Kubernetes.

Bonnes pratiques :
- ✅ Utilisez un token avec les permissions minimales
- ✅ Révocez le token si compromis
- ✅ Limitez l'accès SSH à k8s-master
- ✅ Surveillez les logs du runner
- ✅ Activez l'authentification 2FA sur GitHub

---

## Ressources

- [Documentation GitHub Actions Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Image Docker github-runner](https://github.com/myoung34/docker-github-actions-runner)
