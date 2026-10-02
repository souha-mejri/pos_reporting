# 🔄 Guide : Transférer des fichiers Windows → Linux (SSH)

## 🎯 Problèmes courants et solutions

### ❌ Problème 1 : Caractères corrompus (`: devient çé, â)

**Cause** : Encodage UTF-8 mal géré entre Windows et Linux via SSH

**Solutions** :

#### Option A : SCP (recommandé) ✅
```powershell
# Sur Windows PowerShell
scp C:\Users\msi\Desktop\fichier.yaml master@192.168.158.206:/tmp/

# Puis sur Linux SSH
sudo mv /tmp/fichier.yaml /destination/finale/
```

#### Option B : Heredoc (copier-coller direct)
```bash
# Sur Linux, colle cette commande complète :
cat << 'EOF' | sudo tee /etc/netplan/50-cloud-init.yaml
network:
  version: 2
  ethernets:
    ens33:
      addresses: [192.168.158.206/24]
EOF
```

#### Option C : Nano avec précautions
```bash
# 1. Ouvre nano D'ABORD
sudo nano /etc/netplan/50-cloud-init.yaml

# 2. ATTENDS de voir l'écran bleu avec "^X Exit" en bas

# 3. Colle avec CLIC DROIT (pas Ctrl+V)
```

### ❌ Problème 2 : Le texte colle dans le terminal (pas dans nano)

**Cause** : Tu as collé avant que nano soit ouvert

**Solution** : Vérifie que tu vois bien l'interface nano (écran bleu) AVANT de coller

### ❌ Problème 3 : Commandes SSH déconnectent

**Solution** : Utilise `screen` ou `tmux`
```bash
# Installe screen
sudo apt install screen -y

# Lance une session
screen -S deploy

# Si tu te déconnectes, reconnecte avec :
screen -r deploy
```

## 🚀 Workflow recommandé pour Kubernetes

### Étape 1 : Préparer sur Windows

```powershell
# Ouvre PowerShell dans le dossier kubernetes/
cd C:\chemin\vers\projet\kubernetes

# Vérifie que les fichiers existent
ls

# Devrait afficher :
# deployment.yaml
# service-ingress.yaml
# pvc.yaml
# namespace.yaml
# deploy.sh
# README.md
```

### Étape 2 : Transférer vers le master

```powershell
# Transfert du dossier complet
scp -r * master@192.168.158.206:~/kubernetes/

# Ou fichier par fichier
scp deployment.yaml master@192.168.158.206:~/kubernetes/
scp service-ingress.yaml master@192.168.158.206:~/kubernetes/
scp pvc.yaml master@192.168.158.206:~/kubernetes/
scp namespace.yaml master@192.168.158.206:~/kubernetes/
scp deploy.sh master@192.168.158.206:~/kubernetes/

# Transfert du .env
scp ..\.env master@192.168.158.206:~/
```

### Étape 3 : Déployer sur Linux

```bash
# SSH vers le master
ssh master@192.168.158.206

# Va dans le dossier
cd ~/kubernetes

# Vérifie que les fichiers sont là
ls -la

# Rend le script exécutable
chmod +x deploy.sh

# Configure les variables
export GITHUB_USER="ton_username"
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"

# Lance le déploiement
./deploy.sh
```

## 🔧 Commandes SCP utiles

### Transférer un fichier
```powershell
# Windows → Linux
scp fichier.txt user@ip:/destination/

# Linux → Windows
scp user@ip:/chemin/fichier.txt C:\destination\
```

### Transférer un dossier
```powershell
# Windows → Linux (récursif)
scp -r dossier/ user@ip:/destination/

# Avec port personnalisé
scp -P 2222 -r dossier/ user@ip:/destination/
```

### Transférer plusieurs fichiers
```powershell
scp fichier1.txt fichier2.txt fichier3.txt user@ip:/destination/
```

## 📝 Édition de fichiers à distance

### Méthode 1 : VS Code Remote SSH (recommandé) ✅

1. **Installe l'extension** : `Remote - SSH` dans VS Code

2. **Connecte-toi** :
   - Ctrl+Shift+P → "Remote-SSH: Connect to Host"
   - Entre : `master@192.168.158.206`

3. **Ouvre le dossier** : `/home/master/kubernetes`

4. **Édite directement** - pas de problème d'encodage !

### Méthode 2 : WinSCP (GUI)

1. Télécharge WinSCP : https://winscp.net/
2. Connecte-toi au serveur
3. Glisse-dépose les fichiers
4. Double-clic pour éditer (utilise l'éditeur intégré)

### Méthode 3 : nano/vim en SSH

```bash
# Avec nano (plus simple)
nano fichier.yaml

# Avec vim (plus puissant)
vim fichier.yaml
```

## 🛠️ Troubleshooting

### Erreur : Permission denied

```powershell
# Ajoute ta clé SSH
ssh-keygen -t rsa -b 4096
ssh-copy-id master@192.168.158.206

# Teste
ssh master@192.168.158.206 "echo OK"
```

### Erreur : Connection refused

```bash
# Vérifie que SSH est actif sur le serveur
sudo systemctl status ssh

# Démarre si nécessaire
sudo systemctl start ssh
sudo systemctl enable ssh
```

### Encodage bizarre dans nano

```bash
# Vérifie l'encodage du terminal
echo $LANG
# Devrait afficher : en_US.UTF-8 ou fr_FR.UTF-8

# Change si nécessaire
export LANG=en_US.UTF-8
```

### Le fichier n'apparaît pas après scp

```bash
# Vérifie où il est
find ~ -name "fichier.yaml" -type f

# Vérifie les permissions
ls -la /destination/fichier.yaml
```

## ✅ Checklist finale

Avant de transférer :
- [ ] Fichiers en UTF-8 (sans BOM)
- [ ] Retours à la ligne Unix (LF, pas CRLF)
- [ ] Pas d'espaces dans les noms de fichiers
- [ ] Connexion SSH testée

Après transfert :
- [ ] Fichiers présents : `ls -la`
- [ ] Permissions OK : `chmod +x *.sh`
- [ ] Contenu correct : `cat fichier.yaml`
- [ ] Encodage OK : `file fichier.yaml` (devrait dire "UTF-8")

## 🎓 Bonnes pratiques

1. **Toujours utiliser SCP** pour les fichiers de config
2. **Jamais copier-coller de gros textes** dans le terminal SSH
3. **Utiliser VS Code Remote SSH** pour l'édition
4. **Vérifier l'encodage UTF-8** avant transfert
5. **Faire des backups** avant de modifier des configs système
6. **Tester avec `--dry-run`** avant d'appliquer sur Kubernetes

## 📚 Ressources

- [Documentation SCP](https://man.openbsd.org/scp)
- [VS Code Remote SSH](https://code.visualstudio.com/docs/remote/ssh)
- [WinSCP](https://winscp.net/eng/docs/start)
- [Nano cheatsheet](https://www.nano-editor.org/dist/latest/cheatsheet.html)
