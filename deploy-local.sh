#!/bin/bash

# Local Deployment Script
# This script pushes changes to GitHub and triggers automatic deployment

set -e

echo "🚀 Starting local deployment..."

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    print_warning "No changes to commit"
else
    print_status "Committing changes..."
    git add .
    read -p "Enter commit message: " commit_message
    git commit -m "$commit_message"
fi

# Push to GitHub
print_status "Pushing to GitHub..."
git push origin master

print_success "✅ Code pushed to GitHub!"
print_status "🔄 GitHub Actions will automatically deploy to the server..."

# Optional: Direct deployment to server
read -p "Do you want to deploy directly to server now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "🚀 Deploying directly to server..."
    
    # Deploy to server
    ssh -i ~/.ssh/id_hosting administrator@45.154.238.102 << 'EOF'
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
EOF
    
    print_success "✅ Direct deployment completed!"
fi

print_success "🎉 Deployment process completed!"
echo "🌐 Your application will be available at: https://test.nexonsolutions.be" 