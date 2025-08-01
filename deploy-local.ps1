# Local Deployment Script for Windows
# This script pushes changes to GitHub and triggers automatic deployment

Write-Host "🚀 Starting local deployment..." -ForegroundColor Green

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "❌ Error: Not in a git repository" -ForegroundColor Red
    exit 1
}

# Check if there are changes to commit
$status = git status --porcelain
if ([string]::IsNullOrEmpty($status)) {
    Write-Host "⚠️  No changes to commit" -ForegroundColor Yellow
} else {
    Write-Host "📝 Committing changes..." -ForegroundColor Blue
    git add .
    $commitMessage = Read-Host "Enter commit message"
    git commit -m $commitMessage
}

# Push to GitHub
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Blue
git push origin master

Write-Host "✅ Code pushed to GitHub!" -ForegroundColor Green
Write-Host "🔄 GitHub Actions will automatically deploy to the server..." -ForegroundColor Blue

# Optional: Direct deployment to server
$deployNow = Read-Host "Do you want to deploy directly to server now? (y/n)"
if ($deployNow -eq "y" -or $deployNow -eq "Y") {
    Write-Host "🚀 Deploying directly to server..." -ForegroundColor Blue
    
    # Deploy to server
    ssh -i C:\Users\Dverh\.ssh\id_hosting administrator@45.154.238.102 @"
        echo "📋 Updating repository..."
        cd ~/test-grain-nieuwe
        git pull origin master
        
        echo "🚀 Restarting services..."
        if [ -f "start.sh" ]; then
            chmod +x start.sh stop.sh restart.sh logs.sh
            ./restart.sh
        fi
        
        echo "📊 Service status:"
        docker ps
        
        echo "✅ Direct deployment completed!"
"@
    
    Write-Host "✅ Direct deployment completed!" -ForegroundColor Green
}

Write-Host "🎉 Deployment process completed!" -ForegroundColor Green
Write-Host "🌐 Your application will be available at: https://test.nexonsolutions.be" -ForegroundColor Cyan 