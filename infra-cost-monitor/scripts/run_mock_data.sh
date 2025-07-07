#!/bin/bash

# GCP Cost Monitor - Mock Data Runner
# This script runs the mock data generation system

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

# Function to check Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed. Please install Python3 first."
        exit 1
    fi
    print_success "Python3 is installed: $(python3 --version)"
}

# Function to run mock data generator
run_mock_data_generator() {
    print_status "Generating mock data for 1 year with anomalies..."
    
    cd mock-data
    
    # Run the mock data generator
    python3 mock_data_generator.py
    
    print_success "Mock data generated successfully"
}

# Function to verify output files
verify_output_files() {
    print_status "Verifying output files..."
    
    cd mock-data/output
    
    # Check if all required files exist
    required_files=("composite_data.json" "daily_total_data.json" "mtd_data.json" "anomalies.json" "summary.json")
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "✅ $file exists"
        else
            print_error "❌ $file missing"
        fi
    done
    
    # Show file sizes
    echo ""
    print_status "Output file sizes:"
    ls -lh *.json
}

# Function to show sample data
show_sample_data() {
    print_status "Showing sample of generated data..."
    
    cd mock-data/output
    
    echo ""
    echo "📊 Sample Daily Costs (last 5 days):"
    jq '.[:5]' daily_total_data.json 2>/dev/null || echo "  (jq not available - check file manually)"
    
    echo ""
    echo "📈 Sample MTD Data:"
    jq '.[:3]' mtd_data.json 2>/dev/null || echo "  (jq not available - check file manually)"
    
    echo ""
    echo "🔍 Anomalies Detected:"
    jq 'length' anomalies.json 2>/dev/null || echo "  (check anomalies.json manually)"
}

# Main execution
main() {
    echo ""
    echo "🎲 GCP Cost Monitor - Mock Data Generator"
    echo "========================================="
    echo ""
    echo "This will:"
    echo "  • Generate 1 year of realistic GCP cost data"
    echo "  • Create anomalies for testing"
    echo "  • Generate all required JSON files"
    echo "  • Use realistic enterprise cost ranges"
    echo ""
    
    # Check prerequisites
    check_python
    
    # Run mock data generation
    run_mock_data_generator
    
    # Verify and show results
    verify_output_files
    show_sample_data
    
    echo ""
    echo "🎉 Mock data generation completed!"
    echo "📁 Output files saved to: mock-data/output/"
    echo ""
    echo "Next steps:"
    echo "  • Run AI/ML pipeline: ./scripts/run_ai_pipeline.sh"
    echo "  • Start alert system: ./scripts/run_alert_system.sh"
    echo "  • Start dashboard: ./scripts/run_dashboard.sh"
    echo "  • Start Slack bot: ./scripts/run_slack_bot.sh"
    echo "  • Run complete system: ./scripts/run_complete_system.sh"
    echo ""
}

# Run main function
main 