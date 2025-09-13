#!/bin/bash

# Quick deployment script for Coffee Machine Controller Add-on
# Usage: ./deploy.sh [github-username]

set -e

GITHUB_USER=${1:-"your-username"}
REPO_NAME="coffee-machine-controller-addon"

echo "🚀 Deploying Coffee Machine Controller Add-on..."
echo "GitHub Username: $GITHUB_USER"
echo "Repository: $REPO_NAME"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Initializing..."
    git init
    git add .
    git commit -m "Initial commit"
fi

# Check if remote exists
if ! git remote | grep -q origin; then
    echo "🔗 Adding GitHub remote..."
    git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
fi

# Update configuration files with actual username
echo "⚙️ Updating configuration files..."
sed -i "s/your-username/$GITHUB_USER/g" config.yaml README_ADDON.md repository.yaml 2>/dev/null || \
sed "s/your-username/$GITHUB_USER/g" config.yaml > config.yaml.tmp && mv config.yaml.tmp config.yaml

# Check if icon exists
if [ ! -f "icon.png" ] || [ ! -s "icon.png" ]; then
    echo "⚠️  WARNING: You need to add a proper icon.png file (512x512 PNG)"
    echo "   Current icon.png is just a placeholder text file"
fi

# Stage all changes
echo "📦 Staging changes..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Configure Add-on for deployment

- Updated GitHub username in configuration files
- Ready for Home Assistant Add-on deployment
- Automated build workflow included"
fi

echo "🌍 Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✅ Deployment setup complete!"
echo ""
echo "Next steps:"
echo "1. Go to https://github.com/$GITHUB_USER/$REPO_NAME"
echo "2. Add a proper icon.png file (512x512 PNG)"
echo "3. Create a release (e.g., v1.0.0) to trigger builds"
echo "4. Add the repository to Home Assistant:"
echo "   https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""
echo "🎉 Your Coffee Machine Controller Add-on will be ready!"