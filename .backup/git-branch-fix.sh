#!/bin/bash

# Quick fix for git branch issues

echo "🔧 Fixing git branch issues..."

# Check current status
echo "📋 Current git status:"
git status

echo ""
echo "📋 Current branch:"
git branch

echo ""
echo "📋 Remote branches:"
git branch -r 2>/dev/null || echo "No remote branches"

# Get the current branch name
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
echo ""
echo "ℹ️  Current branch: $CURRENT_BRANCH"

# If we're on master, rename to main
if [ "$CURRENT_BRANCH" = "master" ]; then
    echo "🔄 Renaming master to main..."
    git branch -m main
    CURRENT_BRANCH="main"
fi

# Check if remote exists
if git remote get-url origin >/dev/null 2>&1; then
    echo "✅ Remote origin exists: $(git remote get-url origin)"
    
    # Try different push strategies
    echo ""
    echo "🚀 Trying to push..."
    
    # Method 1: Standard push
    if git push -u origin "$CURRENT_BRANCH" 2>/dev/null; then
        echo "✅ Push successful!"
    elif git push -u origin HEAD:"$CURRENT_BRANCH" 2>/dev/null; then
        echo "✅ Push successful with HEAD reference!"
    elif git push -u origin "$CURRENT_BRANCH" --force 2>/dev/null; then
        echo "✅ Force push successful!"
    else
        echo "❌ All push methods failed"
        echo ""
        echo "🔧 Manual fix options:"
        echo ""
        echo "1. Check if repository exists:"
        echo "   gh repo view $(git remote get-url origin | sed 's/.*github.com[\/:]//;s/.git$//')"
        echo ""
        echo "2. Create repository if it doesn't exist:"
        echo "   gh repo create $(basename $(git remote get-url origin .git)) --public"
        echo ""
        echo "3. Force push to create branch:"
        echo "   git push -u origin $CURRENT_BRANCH --force"
        echo ""
        echo "4. Or delete and recreate repository:"
        echo "   gh repo delete $(git remote get-url origin | sed 's/.*github.com[\/:]//;s/.git$//')"
        echo "   gh repo create $(basename $(git remote get-url origin .git)) --public"
        echo ""
        
        exit 1
    fi
    
    # Push tags if they exist
    if git tag -l | grep -q .; then
        echo "🏷️  Pushing tags..."
        git push origin --tags 2>/dev/null || echo "⚠️  Tag push failed"
    fi
    
else
    echo "❌ No remote origin configured"
    echo "Set up remote first:"
    echo "  git remote add origin https://github.com/USERNAME/REPO.git"
    exit 1
fi

echo ""
echo "✅ Git setup complete!"
echo ""
echo "📋 Final status:"
git status --short
echo ""
echo "🔗 Repository: $(git remote get-url origin)"
echo "🌿 Branch: $(git branch --show-current)"
