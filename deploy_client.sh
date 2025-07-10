#!/bin/bash

# Client Chat Interface Deployment Script
# This script deploys the client chat interface to Streamlit Cloud

echo "🚀 Deploying Client Chat Interface..."

# Check if we're in the right directory
if [ ! -f "app_client.py" ]; then
    echo "❌ Error: app_client.py not found. Please run this script from the project root."
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Git repository not found. Please initialize git first."
    exit 1
fi

# Check if all required files exist
required_files=("app_client.py" "client_chat_interface.py" "client_requirements.txt" ".streamlit/config.toml")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: Required file $file not found."
        exit 1
    fi
done

echo "✅ All required files found."

# Add all files to git
echo "📝 Adding files to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Deploy client chat interface - $(date)"

# Push to remote
echo "🚀 Pushing to remote repository..."
git push

echo "✅ Deployment script completed!"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://share.streamlit.io/"
echo "2. Connect your GitHub repository"
echo "3. Set the main file path to: app_client.py"
echo "4. Add environment variables:"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_ANON_KEY" 
echo "   - OPENAI_API_KEY"
echo "5. Deploy!"
echo ""
echo "🌐 Your client app will be available at:"
echo "https://your-app-name.streamlit.app" 