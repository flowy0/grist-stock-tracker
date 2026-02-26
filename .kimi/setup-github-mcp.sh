#!/bin/bash
# GitHub MCP Server Setup Script for Grist Stock Tracker
# This script configures the GitHub MCP server for Kimi Code

set -e

echo "=== GitHub MCP Server Setup ==="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v kimi &> /dev/null; then
    echo "❌ Error: Kimi CLI not found. Please install it first."
    exit 1
fi
echo "✅ Kimi CLI found"

if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx not found. Please install Node.js."
    exit 1
fi
echo "✅ npx found"

if ! command -v gh &> /dev/null; then
    echo "⚠️  Warning: GitHub CLI (gh) not found. It's recommended for authentication."
fi

# Check GitHub authentication
echo ""
echo "Checking GitHub authentication..."
if command -v gh &> /dev/null && gh auth status &> /dev/null; then
    echo "✅ GitHub CLI authenticated"
    GH_USER=$(gh api user -q .login)
    echo "   User: $GH_USER"
else
    echo "⚠️  GitHub CLI not authenticated or not installed"
    echo "   You can still use MCP with a personal access token"
fi

# Ask for setup method
echo ""
echo "Choose setup method:"
echo "1) Using GitHub CLI authentication (recommended if gh is installed)"
echo "2) Using Personal Access Token"
echo "3) Skip (configure manually later)"
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "Setting up GitHub MCP with GitHub CLI..."
        
        # Get token from gh
        if command -v gh &> /dev/null; then
            TOKEN=$(gh auth token)
            if [ -n "$TOKEN" ]; then
                echo "✅ Got token from GitHub CLI"
                
                # Remove existing if any
                kimi mcp remove github 2>/dev/null || true
                
                # Add with token
                kimi mcp add --transport stdio github \
                    --env "GITHUB_TOKEN=$TOKEN" \
                    -- npx -y @github/mcp-server@latest
                
                echo "✅ GitHub MCP server added"
            else
                echo "❌ Could not get token from GitHub CLI"
                exit 1
            fi
        else
            echo "❌ GitHub CLI not installed"
            exit 1
        fi
        ;;
    
    2)
        echo ""
        echo "Please create a GitHub Personal Access Token:"
        echo "  1. Go to: https://github.com/settings/tokens"
        echo "  2. Click 'Generate new token (classic)'"
        echo "  3. Select scopes: repo, workflow"
        echo "  4. Generate and copy the token"
        echo ""
        read -sp "Enter your GitHub token: " TOKEN
        echo ""
        
        if [ -n "$TOKEN" ]; then
            # Remove existing if any
            kimi mcp remove github 2>/dev/null || true
            
            # Add with token
            kimi mcp add --transport stdio github \
                --env "GITHUB_TOKEN=$TOKEN" \
                -- npx -y @github/mcp-server@latest
            
            echo "✅ GitHub MCP server added"
        else
            echo "❌ No token provided"
            exit 1
        fi
        ;;
    
    3)
        echo "Skipping setup. You can configure manually later."
        echo "See: .kimi/github-mcp-setup.md"
        exit 0
        ;;
    
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

# Verify setup
echo ""
echo "Verifying setup..."
if kimi mcp list | grep -q "github"; then
    echo "✅ GitHub MCP server configured"
    echo ""
    echo "Testing connection..."
    if kimi mcp test github 2>/dev/null; then
        echo "✅ Connection successful"
    else
        echo "⚠️  Connection test failed (server may need authentication)"
    fi
else
    echo "❌ GitHub MCP server not found in configuration"
    exit 1
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "You can now use the GitHub MCP server with Kimi:"
echo ""
echo "  kimi --agent-file .kimi/agent.yaml"
echo ""
echo "Available GitHub operations:"
echo "  - Create PRs"
echo "  - List issues"
echo "  - Add comments"
echo "  - Search code"
echo ""
echo "Documentation: .kimi/github-mcp-setup.md"
