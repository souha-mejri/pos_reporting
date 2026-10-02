# Script PowerShell pour déployer depuis Windows vers Kubernetes
# Usage: .\deploy-from-windows.ps1

param(
    [string]$MasterIP = "192.168.158.206",
    [string]$MasterUser = "master",
    [string]$GithubUser = "",
    [string]$GithubToken = ""
)

Write-Host "🚀 Déploiement RestoReport sur Kubernetes" -ForegroundColor Cyan
Write-Host ""

# Vérifier que nous sommes dans le bon dossier
if (-not (Test-Path "deployment.yaml")) {
    Write-Host "❌ Erreur: Ce script doit être exécuté depuis le dossier kubernetes/" -ForegroundColor Red
    exit 1
}

# Demander les identifiants GitHub si non fournis
if ([string]::IsNullOrEmpty($GithubUser)) {
    $GithubUser = Read-Host "GitHub Username"
}

if ([string]::IsNullOrEmpty($GithubToken)) {
    $GithubToken = Read-Host "GitHub Token (ghp_...)" -AsSecureString
    $GithubToken = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($GithubToken)
    )
}

Write-Host ""
Write-Host "📋 Configuration:" -ForegroundColor Yellow
Write-Host "  Master: $MasterUser@$MasterIP"
Write-Host "  GitHub User: $GithubUser"
Write-Host ""

# Tester la connexion SSH
Write-Host "🔍 Test de connexion SSH..." -ForegroundColor Cyan
$testConnection = ssh -o ConnectTimeout=5 "$MasterUser@$MasterIP" "echo OK" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Impossible de se connecter à $MasterUser@$MasterIP" -ForegroundColor Red
    Write-Host "Vérifie que:" -ForegroundColor Yellow
    Write-Host "  - Le serveur est accessible"
    Write-Host "  - SSH est configuré"
    Write-Host "  - Les identifiants sont corrects"
    exit 1
}

Write-Host "✅ Connexion SSH OK" -ForegroundColor Green
Write-Host ""

# Créer le dossier sur le master
Write-Host "📁 Création du dossier kubernetes sur le master..." -ForegroundColor Cyan
ssh "$MasterUser@$MasterIP" "mkdir -p ~/kubernetes"

# Transférer les fichiers YAML
Write-Host "📤 Transfert des fichiers Kubernetes..." -ForegroundColor Cyan

$filesToTransfer = @(
    "namespace.yaml",
    "pvc.yaml",
    "deployment.yaml",
    "service-ingress.yaml",
    "deploy.sh"
)

foreach ($file in $filesToTransfer) {
    if (Test-Path $file) {
        Write-Host "  ↗️  $file" -ForegroundColor Gray
        scp $file "$MasterUser@${MasterIP}:~/kubernetes/" 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ❌ Échec du transfert de $file" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  ⚠️  $file non trouvé (optionnel)" -ForegroundColor Yellow
    }
}

# Transférer le .env si présent
if (Test-Path "../.env") {
    Write-Host "  ↗️  .env" -ForegroundColor Gray
    scp "../.env" "$MasterUser@${MasterIP}:~/.env" 2>&1 | Out-Null
} else {
    Write-Host "  ⚠️  .env non trouvé - tu devras créer le secret manuellement" -ForegroundColor Yellow
}

Write-Host "✅ Transfert terminé" -ForegroundColor Green
Write-Host ""

# Rendre le script exécutable
Write-Host "🔧 Configuration des permissions..." -ForegroundColor Cyan
ssh "$MasterUser@$MasterIP" "chmod +x ~/kubernetes/deploy.sh"

# Éditer le deployment.yaml pour remplacer VOTRE_USER_GITHUB
Write-Host "🔧 Configuration du GitHub user dans deployment.yaml..." -ForegroundColor Cyan
$replaceUserCmd = "sed -i 's/VOTRE_USER_GITHUB/$GithubUser/g' ~/kubernetes/deployment.yaml"
ssh "$MasterUser@$MasterIP" $replaceUserCmd

Write-Host ""
Write-Host "🎯 Prêt à déployer !" -ForegroundColor Green
Write-Host ""
Write-Host "Options:" -ForegroundColor Yellow
Write-Host "  [1] Déployer maintenant (automatique)"
Write-Host "  [2] Déployer manuellement (je vais en SSH)"
Write-Host "  [3] Annuler"
Write-Host ""

$choice = Read-Host "Ton choix (1/2/3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🚀 Lancement du déploiement automatique..." -ForegroundColor Cyan
        Write-Host ""
        
        $deployCmd = @"
cd ~/kubernetes && 
export GITHUB_USER='$GithubUser' && 
export GITHUB_TOKEN='$GithubToken' && 
./deploy.sh
"@
        
        ssh "$MasterUser@$MasterIP" $deployCmd
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✅ Déploiement réussi !" -ForegroundColor Green
            Write-Host ""
            Write-Host "📝 Prochaines étapes:" -ForegroundColor Yellow
            Write-Host "  1. Récupère le NodePort:" -ForegroundColor White
            Write-Host "     ssh $MasterUser@$MasterIP 'kubectl get svc -n ingress-nginx ingress-nginx-controller'" -ForegroundColor Gray
            Write-Host ""
            Write-Host "  2. Ajoute à C:\Windows\System32\drivers\etc\hosts (en admin):" -ForegroundColor White
            Write-Host "     192.168.158.204   pos-reporting.local" -ForegroundColor Gray
            Write-Host ""
            Write-Host "  3. Accède à l'app:" -ForegroundColor White
            Write-Host "     http://pos-reporting.local:NODEPORT" -ForegroundColor Gray
            Write-Host ""
        } else {
            Write-Host ""
            Write-Host "❌ Erreur pendant le déploiement" -ForegroundColor Red
            Write-Host "Connecte-toi en SSH pour debugger:" -ForegroundColor Yellow
            Write-Host "  ssh $MasterUser@$MasterIP" -ForegroundColor Gray
            Write-Host "  cd ~/kubernetes" -ForegroundColor Gray
            Write-Host "  ./deploy.sh" -ForegroundColor Gray
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "📋 Instructions pour déploiement manuel:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "1. Connecte-toi en SSH:" -ForegroundColor White
        Write-Host "   ssh $MasterUser@$MasterIP" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. Va dans le dossier kubernetes:" -ForegroundColor White
        Write-Host "   cd ~/kubernetes" -ForegroundColor Gray
        Write-Host ""
        Write-Host "3. Configure les variables:" -ForegroundColor White
        Write-Host "   export GITHUB_USER='$GithubUser'" -ForegroundColor Gray
        Write-Host "   export GITHUB_TOKEN='$GithubToken'" -ForegroundColor Gray
        Write-Host ""
        Write-Host "4. Lance le déploiement:" -ForegroundColor White
        Write-Host "   ./deploy.sh" -ForegroundColor Gray
        Write-Host ""
    }
    
    "3" {
        Write-Host ""
        Write-Host "❌ Déploiement annulé" -ForegroundColor Yellow
        Write-Host ""
        exit 0
    }
    
    default {
        Write-Host ""
        Write-Host "❌ Choix invalide" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🔍 Commandes utiles:" -ForegroundColor Cyan
Write-Host "  • Voir les pods:  ssh $MasterUser@$MasterIP 'kubectl get pods -n pos-reporting'" -ForegroundColor Gray
Write-Host "  • Voir les logs:  ssh $MasterUser@$MasterIP 'kubectl logs -n pos-reporting -l app=pos-reporting -f'" -ForegroundColor Gray
Write-Host "  • État complet:   ssh $MasterUser@$MasterIP 'kubectl get all -n pos-reporting'" -ForegroundColor Gray
Write-Host ""
