#!/bin/bash

# GCP Cost Monitor - Go Framework Runner
# This script runs the Go framework to connect to BigQuery and fetch real cost data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Function to check if Go is installed
check_go() {
    if ! command -v go &> /dev/null; then
        print_error "Go is not installed. Please install Go first."
        exit 1
    fi
    print_success "Go is installed: $(go version)"
}

# Function to check BigQuery credentials
check_bigquery_credentials() {
    print_status "Checking BigQuery credentials..."
    
    # Check for environment variables
    if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
        print_warning "GOOGLE_CLOUD_PROJECT not set. Please set your GCP project ID."
        print_status "Example: export GOOGLE_CLOUD_PROJECT=your-project-id"
    fi
    
    if [ -z "$BIGQUERY_DATASET" ]; then
        print_warning "BIGQUERY_DATASET not set. Please set your BigQuery dataset."
        print_status "Example: export BIGQUERY_DATASET=your_dataset"
    fi
    
    if [ -z "$BIGQUERY_TABLE" ]; then
        print_warning "BIGQUERY_TABLE not set. Please set your BigQuery table."
        print_status "Example: export BIGQUERY_TABLE=your_table"
    fi
    
    if [ -z "$BIGQUERY_BILLING_EXPORT_TABLE" ]; then
        print_warning "BIGQUERY_BILLING_EXPORT_TABLE not set. Please set your billing export table."
        print_status "Example: export BIGQUERY_BILLING_EXPORT_TABLE=your_billing_table"
    fi
    
    # Check for application default credentials
    if ! gcloud auth application-default print-access-token &> /dev/null; then
        print_warning "Application default credentials not set."
        print_status "Run: gcloud auth application-default login"
    else
        print_success "BigQuery credentials are configured"
    fi
}

# Function to build Go application
build_go_app() {
    print_status "Building Go application..."
    
    cd go-framework
    
    # Install dependencies
    print_status "Installing Go dependencies..."
    go mod tidy
    
    # Build the application
    print_status "Building application..."
    go build -o ../bin/gcp-cost-monitor .
    
    print_success "Go application built successfully"
}

# Function to run Go framework
run_go_framework() {
    print_status "Running Go framework..."
    
    # Create output directory if it doesn't exist
    mkdir -p mock-data/output
    
    # Run the application
    print_status "Starting GCP Cost Monitor (Go Framework)..."
    ./bin/gcp-cost-monitor
    
    print_success "Go framework completed successfully"
}

# Function to run demo
run_demo() {
    print_status "Running Go framework demo..."
    
    cd go-framework
    
    # Build demo
    go build -o ../bin/demo demo.go
    
    # Run demo
    ../bin/demo
    
    print_success "Demo completed successfully"
}

# Main execution
main() {
    echo ""
    echo "🚀 GCP Cost Monitor - Go Framework"
    echo "=================================="
    echo ""
    echo "This will:"
    echo "  • Connect to BigQuery"
    echo "  • Fetch real GCP cost data"
    echo "  • Process and analyze costs"
    echo "  • Generate JSON output files"
    echo "  • Detect anomalies"
    echo ""
    
    # Check prerequisites
    check_go
    check_bigquery_credentials
    
    # Build and run
    build_go_app
    run_go_framework
    
    echo ""
    echo "🎉 Go framework completed!"
    echo "📁 Output files saved to: mock-data/output/"
    echo ""
    echo "Next steps:"
    echo "  • Run AI/ML pipeline: ./scripts/run_ai_pipeline.sh"
    echo "  • Start alert system: ./scripts/run_alert_system.sh"
    echo "  • Start dashboard: ./scripts/run_dashboard.sh"
    echo "  • Start Slack bot: ./scripts/run_slack_bot.sh"
    echo ""
}

# Check if demo mode is requested
if [ "$1" = "demo" ]; then
    echo ""
    echo "🧪 Running Go Framework Demo"
    echo "============================"
    echo ""
    
    check_go
    check_bigquery_credentials
    build_go_app
    run_demo
    
    echo ""
    echo "🎉 Demo completed!"
    echo ""
else
    main
fi 