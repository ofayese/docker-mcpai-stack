#!/bin/bash

# SonarCloud Analysis Script
# Triggers SonarCloud analysis via GitHub Actions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    print_error "Not in a git repository"
    exit 1
fi

# Check if we have a remote origin
if ! git remote get-url origin > /dev/null 2>&1; then
    print_error "No remote origin configured"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
print_status "Current branch: $CURRENT_BRANCH"

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    print_warning "You have uncommitted changes"
    echo "Uncommitted files:"
    git diff --name-only
    echo ""
    read -p "Do you want to commit them first? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Staging all changes..."
        git add .
        read -p "Enter commit message: " COMMIT_MSG
        git commit -m "$COMMIT_MSG"
        print_success "Changes committed"
    else
        print_warning "Proceeding with uncommitted changes..."
    fi
fi

# Check if we're on a branch that triggers SonarCloud
if [[ "$CURRENT_BRANCH" == "main" ]] || [[ "$CURRENT_BRANCH" == "develop" ]]; then
    print_status "Branch '$CURRENT_BRANCH' will trigger SonarCloud analysis"

    # Push to trigger GitHub Actions
    print_status "Pushing to origin/$CURRENT_BRANCH..."
    git push origin "$CURRENT_BRANCH"

    # Get repository info for GitHub Actions URL
    REPO_URL=$(git remote get-url origin)
    REPO_NAME=$(basename "$REPO_URL" .git)
    REPO_OWNER=$(basename "$(dirname "$REPO_URL")")

    # Remove .git suffix if present
    REPO_OWNER=${REPO_OWNER%.git}

    print_success "Push completed!"
    echo ""
    print_status "SonarCloud analysis will be triggered via GitHub Actions"
    echo "Monitor progress at:"
    echo "  GitHub Actions: https://github.com/$REPO_OWNER/$REPO_NAME/actions"
    echo "  SonarCloud: https://sonarcloud.io/organizations/ofayese/projects"

else
    print_warning "Current branch '$CURRENT_BRANCH' does not trigger SonarCloud analysis"
    print_status "SonarCloud analysis is triggered on 'main' and 'develop' branches"
    echo ""
    echo "Options:"
    echo "1. Switch to main/develop branch"
    echo "2. Create a pull request to main"
    echo "3. Push anyway (no SonarCloud analysis)"
    echo ""
    read -p "What would you like to do? (1/2/3): " -n 1 -r
    echo ""

    case $REPLY in
        1)
            print_status "Available branches:"
            git branch -a
            echo ""
            read -p "Enter branch name (main/develop): " TARGET_BRANCH
            if git show-ref --verify --quiet refs/heads/"$TARGET_BRANCH"; then
                git checkout "$TARGET_BRANCH"
                git pull origin "$TARGET_BRANCH"
                print_success "Switched to $TARGET_BRANCH"

                # Merge current branch if different
                if [[ "$TARGET_BRANCH" != "$CURRENT_BRANCH" ]]; then
                    read -p "Merge $CURRENT_BRANCH into $TARGET_BRANCH? (y/N): " -n 1 -r
                    echo ""
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        git merge "$CURRENT_BRANCH"
                        print_success "Merged $CURRENT_BRANCH into $TARGET_BRANCH"
                    fi
                fi

                # Push to trigger analysis
                git push origin "$TARGET_BRANCH"
                print_success "SonarCloud analysis triggered!"
            else
                print_error "Branch '$TARGET_BRANCH' does not exist"
                exit 1
            fi
            ;;
        2)
            print_status "Push current branch and create PR manually at:"
            git push origin "$CURRENT_BRANCH"
            echo "  https://github.com/$REPO_OWNER/$REPO_NAME/compare/$CURRENT_BRANCH"
            ;;
        3)
            git push origin "$CURRENT_BRANCH"
            print_warning "Pushed without triggering SonarCloud analysis"
            ;;
        *)
            print_error "Invalid option"
            exit 1
            ;;
    esac
fi

print_success "Script completed successfully!"
