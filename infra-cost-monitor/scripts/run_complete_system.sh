#!/bin/bash

# GCP Cost Monitor - Complete System Runner
# This script runs the entire cost monitoring system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print functions
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
    echo -e "${CYAN}[DASHBOARD]${NC} $1"
}

print_ai() {
    echo -e "${PURPLE}[AI/ML]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "README.md" ]; then
        print_error "Please run this script from the infra-cost-monitor directory"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Install AI/ML dependencies
    if [ -f "ai_ml/requirements.txt" ]; then
        pip3 install -r ai_ml/requirements.txt
    fi
    
    # Install dashboard dependencies
    if [ -f "dashboard/requirements.txt" ]; then
        pip3 install -r dashboard/requirements.txt
    fi
    
    # Install Slack bot dependencies
    if [ -f "slack_bot/requirements.txt" ]; then
        pip3 install -r slack_bot/requirements.txt
    fi
    
    print_success "Python dependencies installed"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment files..."
    
    # Create necessary directories
    mkdir -p data/logs
    mkdir -p mock-data/output
    mkdir -p ai_ml/forecasts
    
    # Copy config files if they don't exist
    if [ ! -f "config/alert_thresholds.json" ]; then
        cp config/alert_thresholds_backup.json config/alert_thresholds.json 2>/dev/null || echo '{"cost_spike_threshold": 1.0, "cost_spike_percentage": 10.0, "anomaly_threshold": 2.0}' > config/alert_thresholds.json
    fi
    
    print_success "Environment setup completed"
}

# Function to run Go framework (real BigQuery data)
run_go_framework() {
    print_status "Step 1: Running Go framework (BigQuery integration)..."
    
    if [ -f "scripts/run_go_framework.sh" ]; then
        chmod +x scripts/run_go_framework.sh
        ./scripts/run_go_framework.sh
    else
        print_warning "Go framework not available - using mock data instead"
        run_mock_data_generator
    fi
}

# Function to run mock data generator
run_mock_data_generator() {
    print_status "Step 1: Generating mock data for 1 year with anomalies..."
    
    if [ -f "mock-data/scripts/mock_data_generator.py" ]; then
        cd mock-data
        python3 scripts/mock_data_generator.py
        cd ..
        print_success "Mock data generated."
    else
        print_error "Mock data generator not found at mock-data/scripts/mock_data_generator.py"
        print_error "Current directory: $(pwd)"
        print_error "Available files in mock-data/scripts/:"
        ls -la mock-data/scripts/ 2>/dev/null || print_error "mock-data/scripts/ directory not found"
        exit 1
    fi
}

# Function to run AI/ML pipeline
run_ai_pipeline() {
    print_status "Step 2: Running AI/ML pipeline..."
    
    if [ -f "ai_ml/cost_ai_pipeline.py" ]; then
        cd ai_ml
        python3 cost_ai_pipeline.py
        cd ..
        print_success "AI/ML pipeline completed - Vector database populated"
    else
        print_error "AI/ML pipeline not found"
        exit 1
    fi
}

# Function to start alert system
start_alert_system() {
    print_status "Step 3: Starting alert system..."
    
    if [ -f "alert_system/alert_manager.py" ]; then
        cd alert_system
        python3 alert_manager.py &
        ALERT_PID=$!
        echo $ALERT_PID > ../data/alert_system.pid
        cd ..
        print_success "Alert system started (PID: $ALERT_PID)"
    else
        print_error "Alert system not found"
        exit 1
    fi
}

# Function to trigger alerts
trigger_alerts() {
    print_status "Step 3.5: Triggering alerts for anomalies..."
    
    # Wait a moment for alert system to start
    sleep 2
    
    # Run the alert triggering script
    python3 -c "
import json
import os
import sys
sys.path.append('alert_system')
from alert_manager import AlertManager, AlertConfig

# Load config
with open('alert_system/config.json', 'r') as f:
    config_data = json.load(f)
config = AlertConfig(**config_data)

# Initialize alert manager
alert_manager = AlertManager(config)

# Load anomalies
with open('mock-data/output/anomalies.json', 'r') as f:
    anomalies = json.load(f)

print(f'Found {len(anomalies)} anomalies')

# Process each anomaly
for i, anomaly in enumerate(anomalies, 1):
    print(f'Processing anomaly {i}: {anomaly[\"service\"]} - ₹{anomaly[\"cost_impact\"]:.2f}')
    alert = alert_manager.check_anomaly(anomaly)
    if alert:
        print(f'  ✅ Alert triggered!')
        success = alert_manager.send_alert(alert)
        if success:
            print(f'  📤 Alert sent successfully')
        else:
            print(f'  ❌ Failed to send alert')
    else:
        print(f'  ⚠️  No alert triggered')
    
    # Small delay between processing
    import time
    time.sleep(1)

print('🎉 All alerts processed!')
"
    
    print_success "Alerts triggered successfully"
}

# Function to start web dashboard
start_dashboard() {
    print_status "Step 4: Starting web dashboard..."
    
    if [ -f "dashboard/app.py" ]; then
        cd dashboard
        python3 app.py &
        DASHBOARD_PID=$!
        echo $DASHBOARD_PID > ../data/dashboard.pid
        cd ..
        
        # Wait for dashboard to start
        print_status "Waiting for dashboard to start..."
        sleep 5
        
        # Check if dashboard is running
        if curl -s "http://localhost:5001/health" >/dev/null 2>&1; then
            print_dashboard "Dashboard is running at http://localhost:5001"
        else
            print_warning "Dashboard may not be running properly"
        fi
    else
        print_error "Dashboard not found"
        exit 1
    fi
}

# Function to start Ollama LLM
start_ollama() {
    print_status "Step 5: Starting Ollama LLM service..."
    
    # Check if Ollama is already running
    if pgrep -x "ollama" > /dev/null; then
        print_success "Ollama is already running"
    else
        print_warning "Ollama not found. Please install and start Ollama manually."
        print_status "Install from: https://ollama.ai"
    fi
}

# Function to start Slack bot
start_slack_bot() {
    print_status "Step 6: Starting Slack bot..."
    
    if [ -f "slack_bot/slack_bot.py" ]; then
        cd slack_bot
        
        # Apply SQLite patch if needed
        if [ -f "run_slack_bot_wrapper.py" ]; then
            print_status "Starting Slack bot with SQLite patch..."
            python3 run_slack_bot_wrapper.py &
        else
            print_status "Starting Slack bot..."
            python3 slack_bot.py &
        fi
        
        SLACK_PID=$!
        echo $SLACK_PID > ../data/slack_bot.pid
        cd ..
        
        print_success "Slack bot started (PID: $SLACK_PID)"
        print_status "Bot will be available in Slack as @Cosmos"
        print_status "Use /cost-help for available commands"
    else
        print_error "Slack bot not found"
        exit 1
    fi
}

# Function to show system status
show_system_status() {
    echo ""
    echo "🎯 System Status"
    echo "================"
    
    # Check if processes are running
    if [ -f "data/alert_system.pid" ]; then
        ALERT_PID=$(cat data/alert_system.pid)
        if ps -p $ALERT_PID > /dev/null; then
            print_status "  • Alert System: ✅ Running (PID: $ALERT_PID)"
        else
            print_warning "  • Alert System: ❌ Not running"
        fi
    fi
    
    if [ -f "data/dashboard.pid" ]; then
        DASHBOARD_PID=$(cat data/dashboard.pid)
        if ps -p $DASHBOARD_PID > /dev/null; then
            print_status "  • Web Dashboard: ✅ http://localhost:5001"
        else
            print_warning "  • Web Dashboard: ❌ Not running"
        fi
    fi
    
    if [ -f "data/slack_bot.pid" ]; then
        SLACK_PID=$(cat data/slack_bot.pid)
        if ps -p $SLACK_PID > /dev/null; then
            print_status "  • Slack Bot: ✅ Running (PID: $SLACK_PID)"
        else
            print_warning "  • Slack Bot: ❌ Not running"
        fi
    fi
    
    if pgrep -x "ollama" > /dev/null; then
        print_status "  • Ollama LLM: ✅ Running"
    else
        print_warning "  • Ollama LLM: ❌ Not running"
    fi
    
    echo ""
    print_status "📊 Data Sources:"
    if [ -f "mock-data/output/composite_data.json" ]; then
        print_status "  • Cost Data: ✅ Available"
    else
        print_warning "  • Cost Data: ❌ Not available"
    fi
    
    if [ -f "ai_ml/forecasts/" ]; then
        print_status "  • Forecasts: ✅ Available"
    else
        print_warning "  • Forecasts: ❌ Not available"
    fi
    
    echo ""
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    
    # Kill background processes
    if [ -f "data/alert_system.pid" ]; then
        ALERT_PID=$(cat data/alert_system.pid)
        kill $ALERT_PID 2>/dev/null || true
        rm -f data/alert_system.pid
    fi
    
    if [ -f "data/dashboard.pid" ]; then
        DASHBOARD_PID=$(cat data/dashboard.pid)
        kill $DASHBOARD_PID 2>/dev/null || true
        rm -f data/dashboard.pid
    fi
    
    if [ -f "data/slack_bot.pid" ]; then
        SLACK_PID=$(cat data/slack_bot.pid)
        kill $SLACK_PID 2>/dev/null || true
        rm -f data/slack_bot.pid
    fi
    
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo ""
    echo "🚀 GCP Cost Monitor - Complete System"
    echo "====================================="
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --go-framework    Use Go framework (BigQuery integration)"
    echo "  --mock-data       Use mock data generator (default)"
    echo "  --demo            Run Go framework demo"
    echo "  --status          Show system status"
    echo "  --cleanup         Cleanup background processes"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run with mock data"
    echo "  $0 --go-framework     # Run with real BigQuery data"
    echo "  $0 --demo             # Run Go framework demo"
    echo "  $0 --status           # Show system status"
    echo ""
}

# Main execution
main() {
    # Parse command line arguments
    DATA_SOURCE="mock"
    DEMO_MODE=false
    STATUS_MODE=false
    CLEANUP_MODE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --go-framework)
                DATA_SOURCE="go"
                shift
                ;;
            --mock-data)
                DATA_SOURCE="mock"
                shift
                ;;
            --demo)
                DEMO_MODE=true
                shift
                ;;
            --status)
                STATUS_MODE=true
                shift
                ;;
            --cleanup)
                CLEANUP_MODE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Handle different modes
    if [ "$CLEANUP_MODE" = true ]; then
        cleanup
        exit 0
    fi
    
    if [ "$STATUS_MODE" = true ]; then
        show_system_status
        exit 0
    fi
    
    if [ "$DEMO_MODE" = true ]; then
        echo ""
        echo "🧪 Running Go Framework Demo"
        echo "============================"
        echo ""
        
        check_prerequisites
        install_dependencies
        setup_environment
        
        if [ -f "scripts/run_go_framework.sh" ]; then
            chmod +x scripts/run_go_framework.sh
            ./scripts/run_go_framework.sh demo
        else
            print_error "Go framework demo not available"
            exit 1
        fi
        
        exit 0
    fi
    
    # Main execution
    echo ""
    echo "🚀 Starting GCP Cost Monitor System..."
    echo "======================================"
    echo ""
    
    if [ "$DATA_SOURCE" = "go" ]; then
        echo "Components:"
        echo "  • Go Framework (BigQuery integration)"
        echo "  • AI/ML Pipeline (anomaly detection + forecasting)"
        echo "  • Alert System (Slack + email notifications)"
        echo "  • Web Dashboard (http://localhost:5001)"
        echo "  • Ollama LLM (for natural language queries)"
        echo "  • Slack Bot (for cost queries and alerts)"
        echo ""
        echo "Note: Using real BigQuery data"
        echo "      (Requires GCP credentials and BigQuery setup)"
        echo ""
    else
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
    fi
    
    # Setup and run
    check_prerequisites
    install_dependencies
    setup_environment
    
    # Run data source
    if [ "$DATA_SOURCE" = "go" ]; then
        run_go_framework
    else
        run_mock_data_generator
    fi
    
    # Run remaining components
    run_ai_pipeline
    start_alert_system
    trigger_alerts # Added this line
    start_dashboard
    start_ollama
    start_slack_bot
    
    # Show final status
    show_system_status
    
    echo ""
    echo "🎉 System started successfully!"
    echo ""
    echo "Access points:"
    echo "  • Web Dashboard: http://localhost:5001"
    echo "  • Slack Bot: @Cosmos (in your Slack workspace)"
    echo "  • Ollama LLM: http://localhost:11434"
    echo ""
    echo "Commands:"
    echo "  • Check status: $0 --status"
    echo "  • Cleanup: $0 --cleanup"
    echo "  • Run with real data: $0 --go-framework"
    echo "  • Run demo: $0 --demo"
    echo ""
}

# Run main function
main "$@" 