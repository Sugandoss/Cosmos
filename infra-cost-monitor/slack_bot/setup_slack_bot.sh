#!/bin/bash

# GCP Cost Monitor - Slack Bot Setup Script
# This script helps you set up and run the Slack bot

set -e

echo "🤖 GCP Cost Monitor - Slack Bot Setup"
echo "====================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if we're in the right directory
if [ ! -f "slack_bot.py" ]; then
    print_error "Please run this script from the slack_bot directory"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

print_status "Checking dependencies..."

# Install dependencies
if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    echo
    echo "📋 Slack Bot Setup Instructions:"
    echo "================================"
    echo
    echo "1. Create a Slack App:"
    echo "   • Go to https://api.slack.com/apps"
    echo "   • Click 'Create New App'"
    echo "   • Choose 'From scratch'"
    echo "   • Name: 'GCP Cost Monitor'"
    echo "   • Select your workspace"
    echo
    echo "2. Configure Bot Token Scopes:"
    echo "   • Go to 'OAuth & Permissions'"
    echo "   • Add these Bot Token Scopes:"
    echo "     - app_mentions:read"
    echo "     - chat:write"
    echo "     - commands"
    echo "     - im:history"
    echo "     - im:read"
    echo "     - im:write"
    echo
    echo "3. Install App to Workspace:"
    echo "   • Click 'Install to Workspace'"
    echo "   • Copy the 'Bot User OAuth Token' (starts with xoxb-)"
    echo
    echo "4. Configure Signing Secret:"
    echo "   • Go to 'Basic Information'"
    echo "   • Copy the 'Signing Secret'"
    echo
    echo "5. Enable Socket Mode:"
    echo "   • Go to 'Socket Mode'"
    echo "   • Enable Socket Mode"
    echo "   • Create an App-Level Token (starts with xapp-)"
    echo
    echo "6. Add Slash Commands:"
    echo "   • Go to 'Slash Commands'"
    echo "   • Add these commands:"
    echo "     - /cost-query (Description: Ask about GCP costs)"
    echo "     - /cost-stats (Description: Get cost statistics)"
    echo "     - /cost-help (Description: Show help)"
    echo
    echo "7. Create .env file:"
    echo "   • Copy env_example.txt to .env"
    echo "   • Fill in your tokens"
    echo
    echo "8. Run the bot:"
    echo "   • python3 slack_bot.py"
    echo
    read -p "Press Enter when you've completed the setup..."
    
    if [ ! -f ".env" ]; then
        print_error ".env file still not found. Please create it with your Slack credentials."
        exit 1
    fi
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install -r requirements.txt
print_success "Dependencies installed"

# Check if AI/ML pipeline has been run
if [ ! -d "../ai_ml/chroma_db" ]; then
    print_warning "Chroma database not found. Please run the AI/ML pipeline first:"
    echo "   cd ../ai_ml && ./run_ai_pipeline.sh"
    echo
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if Ollama is running
if command -v ollama &> /dev/null; then
    if ollama list &> /dev/null; then
        print_success "Ollama is running and available"
    else
        print_warning "Ollama is not running. Start it with: ollama serve"
    fi
else
    print_warning "Ollama not found. Install it for LLM features: https://ollama.ai"
fi

echo
print_success "🎉 Slack Bot setup complete!"
echo
echo "🚀 To start the bot:"
echo "   python3 slack_bot.py"
echo
echo "📋 Bot Features:"
echo "   • @mention the bot to ask questions"
echo "   • Send direct messages"
echo "   • Use /cost-query command"
echo "   • Use /cost-stats command"
echo "   • Use /cost-help command"
echo
echo "🔗 Example Usage:"
echo "   @bot Which services are most expensive?"
echo "   /cost-query Show me recent anomalies"
echo "   /cost-stats" 