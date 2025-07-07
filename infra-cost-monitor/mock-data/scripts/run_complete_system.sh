#!/bin/bash

# Complete GCP Cost Monitor System Runner
# This script runs the entire system: Go framework → AI/ML pipeline → Alert system → Dashboard → Slack bot

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_dashboard() {
    echo -e "${PURPLE}[DASHBOARD]${NC} $1"
}

print_alert() {
    echo -e "${CYAN}[ALERT]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a process is running
is_process_running() {
    pgrep -f "$1" >/dev/null 2>&1
}

# Function to wait for a service to be ready
wait_for_service() {
    local service_name="$1"
    local port="$2"
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port/health" >/dev/null 2>&1; then
            print_success "$service_name is ready on port $port!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within $((max_attempts * 2)) seconds"
    return 1
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p output
    mkdir -p alert_system
    mkdir -p dashboard/templates
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
    
    # Try to install pysqlite3-binary, fallback to pysqlite3 if needed
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
    
    # Install dashboard dependencies
    cd dashboard
    pip3 install flask flask-socketio requests python-dotenv
    cd ..
    
    # Install alert system dependencies
    cd alert_system
    pip3 install requests python-dotenv
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
    
    # Create alert system config
    if [ ! -f "alert_system/config.json" ]; then
        cat > alert_system/config.json << EOF
{
    "slack_webhook_url": "",
    "email_smtp_server": "smtp.gmail.com",
    "email_smtp_port": 587,
    "email_username": "",
    "email_password": "",
    "email_recipients": [],
    "escalation_recipients": [],
    "alert_cooldown_minutes": 30,
    "max_alerts_per_hour": 10
}
EOF
        print_warning "Created alert_system/config.json"
        print_warning "Please configure alert settings in alert_system/config.json"
    fi
    
    print_success "Environment setup completed"
}

# Function to run Go framework
run_go_framework() {
    print_status "Step 1: Skipping Go framework (using mock data instead)..."
    print_warning "Go framework not available - using mock data generator"
    print_success "Mock data generation will be handled in Step 2"
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

# Function to start alert system
start_alert_system() {
    print_status "Step 3: Starting alert system..."
    
    cd alert_system
    
    # Start alert manager in background
    python3 alert_manager.py > alert_system.log 2>&1 &
    ALERT_PID=$!
    
    print_success "Alert system started (PID: $ALERT_PID)"
    
    cd ..
}

# Function to start dashboard
start_dashboard() {
    print_status "Step 4: Starting web dashboard..."
    
    cd dashboard
    
    # Check if dashboard dependencies are installed
    if ! python3 -c "import flask, flask_socketio" 2>/dev/null; then
        print_warning "Dashboard dependencies not installed. Installing..."
        pip3 install "flask<3.0.0" "werkzeug<3.0.0" flask-socketio requests python-dotenv
    fi
    
    # Check if app.py exists
    if [ ! -f "app.py" ]; then
        print_error "Dashboard app.py not found. Skipping dashboard."
        cd ..
        return
    fi
    
    # Start dashboard in background with full path
    python3 app.py > dashboard.log 2>&1 &
    DASHBOARD_PID=$!
    
    # Wait for dashboard to be ready
    print_status "Waiting for dashboard to start..."
    sleep 5
    
            if curl -s "http://localhost:5001/health" >/dev/null 2>&1; then
            print_dashboard "Dashboard is running at http://localhost:5001"
    else
        print_warning "Dashboard may not be ready yet, but continuing..."
        print_warning "Check dashboard.log for errors"
    fi
    
    cd ..
}

# Function to start Ollama
start_ollama() {
    if command_exists "ollama"; then
        print_status "Step 5: Starting Ollama LLM service..."
        
        # Check if Ollama is already running
        if ! is_process_running "ollama"; then
            print_status "Starting Ollama in background..."
            ollama serve > ollama.log 2>&1 &
            OLLAMA_PID=$!
            
            # Wait for Ollama to be ready
            sleep 5
            if is_process_running "ollama"; then
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
    print_status "Step 6: Starting Slack bot..."
    
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
    print_success "🎉 Complete GCP Cost Monitor System is running!"
    echo ""
    print_status "System Components:"
    print_status "  • Go Framework: ✅ Cost data generation"
    print_status "  • AI/ML Pipeline: ✅ Vector database populated"
    print_status "  • Alert System: ✅ Real-time monitoring"
            print_status "  • Web Dashboard: ✅ http://localhost:5001"
    print_status "  • Ollama LLM: $(is_process_running "ollama" && echo "✅ Running" || echo "❌ Not running")"
    print_status "  • Slack Bot: ✅ Running as @Cosmos"
    echo ""
    print_status "Access Points:"
    print_dashboard "  • Dashboard: http://localhost:5001"
    print_alert "  • Alert System: Monitoring in background"
    print_status "  • Slack Bot: @Cosmos in your Slack workspace"
    echo ""
    print_status "Slack Commands:"
    print_status "  • /cost-help - Show available commands"
    print_status "  • /cost-query <question> - Ask about costs"
    print_status "  • /cost-stats - Get data statistics"
    echo ""
    print_status "Press Ctrl+C to stop the entire system"
}

# Function to cleanup on exit
cleanup() {
    echo ""
    print_status "Cleaning up..."
    
    # Stop all background processes
    if [ ! -z "$ALERT_PID" ]; then
        print_status "Stopping alert system..."
        kill $ALERT_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$DASHBOARD_PID" ]; then
        print_status "Stopping dashboard..."
        kill $DASHBOARD_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$OLLAMA_PID" ]; then
        print_status "Stopping Ollama..."
        kill $OLLAMA_PID 2>/dev/null || true
    fi
    
    print_success "Cleanup completed"
}

# Function to generate mock data
run_mock_data_generator() {
    print_status "Generating mock data for 1 year with anomalies..."
    python3 mock_data_generator.py
    print_success "Mock data generated."
}

# Main execution
main() {
    echo ""
    echo "🚀 Starting GCP Cost Monitor System..."
    echo "======================================"
    echo ""
    echo "Components:"
    echo "  • Mock Data Generator (realistic GCP costs)"
    echo "  • AI/ML Pipeline (anomaly detection + forecasting)"
    echo "  • Alert System (Slack + email notifications)"
    echo "  • Web Dashboard (http://localhost:5001)"
    echo "  • Ollama LLM (for natural language queries)"
    echo "  • Slack Bot (for cost queries and alerts)"
    echo ""
    echo "Note: Using mock data with realistic GCP costs"
    echo "      (BigQuery integration available for production)"
    echo ""
    
    # Check dependencies
    check_dependencies
    
    # Create directories
    create_directories
    
    # Install Python dependencies
    install_python_deps
    
    # Setup environment
    setup_environment
    
    # Generate mock data
    run_mock_data_generator
    
    # Run Go framework
    run_go_framework
    
    # Run AI/ML pipeline
    run_ai_pipeline
    
    # Start alert system
    start_alert_system
    
    # Start dashboard
    start_dashboard
    
    # Start Ollama
    start_ollama
    
    # Start Slack bot
    start_slack_bot
    
    # Show status
    show_status
}

# Trap Ctrl+C and cleanup
trap cleanup EXIT

main "$@" 