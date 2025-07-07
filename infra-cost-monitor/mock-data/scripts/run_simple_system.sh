#!/bin/bash

# Simple GCP Cost Monitor System Runner
# This script runs the core system: Go framework → AI/ML pipeline → Slack bot

set -e  # Exit on any error

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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p output
    mkdir -p ai_ml/chroma_db
    mkdir -p slack_bot
    
    print_success "Directories created"
}

# Function to check and install dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command_exists "go"; then
        missing_deps+=("go")
    fi
    
    if ! command_exists "python3"; then
        missing_deps+=("python3")
    fi
    
    if ! command_exists "pip3"; then
        missing_deps+=("pip3")
    fi
    
    if ! command_exists "ollama"; then
        print_warning "Ollama not found - LLM features will be limited"
        print_warning "Install from: https://ollama.ai"
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_error "Please install missing dependencies before running this script"
        exit 1
    fi
    
    print_success "Dependencies check completed"
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Install core dependencies
    pip3 install flask flask-socketio requests python-dotenv
    
    # Try to install SQLite packages
    if pip3 install pysqlite3-binary 2>/dev/null; then
        print_success "Installed pysqlite3-binary"
    elif pip3 install pysqlite3 2>/dev/null; then
        print_success "Installed pysqlite3 (fallback)"
    else
        print_warning "Could not install pysqlite3 - using system sqlite3"
    fi
    
    # Install AI/ML dependencies
    cd ai_ml
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
    fi
    cd ..
    
    print_success "Python dependencies installed"
}

# Function to setup environment files
setup_environment() {
    print_status "Setting up environment files..."
    
    # Create .env files if they don't exist
    if [ ! -f "slack_bot/.env" ] && [ -f "slack_bot/env_example.txt" ]; then
        cp slack_bot/env_example.txt slack_bot/.env
        print_warning "Created slack_bot/.env from template"
        print_warning "Please edit slack_bot/.env with your Slack tokens"
    fi
    
    print_success "Environment setup completed"
}

# Function to run Go framework
run_go_framework() {
    print_status "Step 1: Running Go framework to generate cost data..."
    
    if [ -f "run.sh" ]; then
        chmod +x run.sh
        ./run.sh
        print_success "Go framework completed - JSON data generated"
    else
        print_error "run.sh not found. Please ensure the Go framework is set up."
        exit 1
    fi
}

# Function to run AI/ML pipeline
run_ai_pipeline() {
    print_status "Step 2: Running AI/ML pipeline to process data..."
    
    cd ai_ml
    
    if [ -f "run_ai_pipeline.sh" ]; then
        chmod +x run_ai_pipeline.sh
        ./run_ai_pipeline.sh
        print_success "AI/ML pipeline completed - Vector database populated"
    elif [ -f "cost_ai_pipeline.py" ]; then
        python3 cost_ai_pipeline.py
        print_success "AI/ML pipeline completed - Vector database populated"
    else
        print_error "Neither run_ai_pipeline.sh nor cost_ai_pipeline.py found in ai_ml directory."
        exit 1
    fi
    
    cd ..
}

# Function to start Ollama
start_ollama() {
    if command_exists "ollama"; then
        print_status "Step 3: Starting Ollama LLM service..."
        
        # Check if Ollama is already running
        if ! pgrep -f "ollama" >/dev/null; then
            print_status "Starting Ollama in background..."
            ollama serve > ollama.log 2>&1 &
            OLLAMA_PID=$!
            
            # Wait for Ollama to be ready
            sleep 5
            if pgrep -f "ollama" >/dev/null; then
                print_success "Ollama started successfully (PID: $OLLAMA_PID)"
            else
                print_warning "Ollama may not be ready yet, but continuing..."
            fi
        else
            print_success "Ollama is already running"
        fi
    else
        print_warning "Ollama not found - LLM features will be limited"
    fi
}

# Function to start Slack bot
start_slack_bot() {
    print_status "Step 4: Starting Slack bot..."
    
    cd slack_bot
    
    # Check if .env file exists and has tokens
    if [ ! -f ".env" ]; then
        print_error ".env file not found in slack_bot directory"
        print_error "Please create .env file with your Slack tokens"
        exit 1
    fi
    
    # Check if tokens are configured
    if grep -q "xoxb-" .env; then
        print_status "Starting Slack bot with SQLite patch..."
        print_status "Bot will be available in Slack as @Cosmos"
        print_status "Use /cost-help for available commands"
    else
        print_error "Slack tokens not configured in .env file"
        print_error "Please add your Slack bot token to .env file"
        exit 1
    fi
    
    # Run the Slack bot (this will keep running)
    python3 run_slack_bot_wrapper.py
    
    cd ..
}

# Function to show system status
show_status() {
    echo ""
    print_success "🎉 Simple GCP Cost Monitor System is running!"
    echo ""
    print_status "System Components:"
    print_status "  • Go Framework: ✅ Cost data generation"
    print_status "  • AI/ML Pipeline: ✅ Vector database populated"
    print_status "  • Ollama LLM: $(pgrep -f "ollama" >/dev/null && echo "✅ Running" || echo "❌ Not running")"
    print_status "  • Slack Bot: ✅ Running as @Cosmos"
    echo ""
    print_status "Access Points:"
    print_status "  • Slack Bot: @Cosmos in your Slack workspace"
    echo ""
    print_status "Slack Commands:"
    print_status "  • /cost-help - Show available commands"
    print_status "  • /cost-query <question> - Ask about costs"
    print_status "  • /cost-stats - Get data statistics"
    echo ""
    print_status "Press Ctrl+C to stop the system"
}

# Function to cleanup on exit
cleanup() {
    echo ""
    print_status "Cleaning up..."
    
    # Stop Ollama if we started it
    if [ ! -z "$OLLAMA_PID" ]; then
        print_status "Stopping Ollama..."
        kill $OLLAMA_PID 2>/dev/null || true
    fi
    
    print_success "Cleanup completed"
}

# Main execution
main() {
    echo "🚀 Starting Simple GCP Cost Monitor System"
    echo "=========================================="
    echo "This will start:"
    echo "  • Go Framework (cost data generation)"
    echo "  • AI/ML Pipeline (vector database)"
    echo "  • Ollama LLM (if available)"
    echo "  • Slack Bot (@Cosmos)"
    echo ""
    
    # Check dependencies
    check_dependencies
    
    # Create directories
    create_directories
    
    # Install Python dependencies
    install_python_deps
    
    # Setup environment
    setup_environment
    
    # Run Go framework
    run_go_framework
    
    # Run AI/ML pipeline
    run_ai_pipeline
    
    # Start Ollama
    start_ollama
    
    # Show system status
    show_status
    
    # Start Slack bot (this will keep running)
    start_slack_bot
    
    # Cleanup on exit
    cleanup
}

# Handle script interruption
trap cleanup SIGINT SIGTERM

# Run main function
main "$@" 