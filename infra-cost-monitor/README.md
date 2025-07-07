# GCP Cost Monitoring & AI/ML Pipeline System

A comprehensive cost monitoring system with AI/ML capabilities for GCP infrastructure, supporting both real BigQuery integration and mock data generation.

## 🏗️ Architecture Overview

The system is organized into two main approaches:

### 1. **Real Data Pipeline** (Go Framework)
- **Location**: `go-framework/`
- **Purpose**: Connect to BigQuery, fetch real GCP cost data
- **Components**: Go adapters, monitors, triggers, data processors
- **Output**: Real cost data from your GCP billing

### 2. **Mock Data Pipeline** (Python Framework)  
- **Location**: `mock-data/`
- **Purpose**: Generate realistic synthetic data for testing
- **Components**: Python mock data generator, AI/ML pipeline
- **Output**: Realistic test data with anomalies

## 📁 Directory Structure

```
infra-cost-monitor/
├── go-framework/                 # Real BigQuery Integration
│   ├── adapters/
│   │   └── bigquery/
│   │       └── client.go        # BigQuery connection & queries
│   ├── vendors/gcp/
│   │   ├── models/
│   │   │   └── cost_data.go     # Cost data structures
│   │   ├── monitors/
│   │   │   ├── daily_monitor.go # Daily cost monitoring
│   │   │   ├── mtd_monitor.go   # Month-to-date monitoring
│   │   │   └── dimensional_monitor.go
│   │   ├── triggers/
│   │   │   └── mtd_triggers.go # Alert triggers
│   │   └── utils/
│   │       ├── data_processor.go # Data processing
│   │       └── json_output.go    # JSON formatting
│   ├── main.go                   # Go application entry point
│   ├── demo.go                   # Demo/test file
│   ├── go.mod                    # Go dependencies
│   └── go.sum                    # Go dependency lock
│
├── mock-data/                    # Mock Data Generation
│   ├── scripts/
│   │   └── mock_data_generator.py # Generate realistic test data
│   └── output/                   # Generated mock data files
│       ├── composite_data.json   # Detailed cost breakdown
│       ├── daily_total_data.json # Daily aggregated costs
│       ├── mtd_data.json        # Month-to-date data
│       ├── anomalies.json        # Anomaly records
│       └── summary.json          # System summary
│
├── ai_ml/                        # AI/ML Pipeline (Works with both)
│   ├── cost_ai_pipeline.py      # Main AI/ML processing
│   ├── cost_forecasting.py      # Cost forecasting (Prophet)
│   ├── forecasts/               # Generated forecasts
│   ├── chroma_db/              # Vector database
│   └── requirements.txt         # Python dependencies
│
├── alert_system/                 # Alert Management
│   ├── alert_manager.py         # Alert processing & notifications
│   └── alert_system.log         # Alert system logs
│
├── dashboard/                    # Web Dashboard
│   ├── app.py                   # Flask dashboard application
│   ├── templates/
│   │   └── dashboard.html       # Dashboard UI
│   └── dashboard.log            # Dashboard logs
│
├── slack_bot/                    # Slack Integration
│   ├── slack_bot.py             # Slack bot implementation
│   ├── rag_integration.py       # RAG for natural language queries
│   ├── requirements.txt          # Bot dependencies
│   └── env_example.txt          # Environment variables template
│
├── config/                       # Configuration Files
│   └── alert_thresholds.json    # Alert configuration
│
├── data/                         # System Data
│   ├── alert_history.json       # Alert history
│   └── logs/                    # System logs
│
├── tests/                        # Test Files
│   ├── test_alerts_direct.py    # Direct alert testing
│   ├── test_anomaly_alert.py    # Anomaly alert testing
│   └── force_alert_test.py      # Force alert testing
│
└── scripts/                      # System Scripts
    ├── run_complete_system.sh   # Run entire system
    ├── run_go_framework.sh      # Run Go framework only
    ├── run_mock_data.sh         # Run mock data only
    └── run_simple_system.sh     # Run simplified system
```

## 🚀 Quick Start

### Option 1: Mock Data (Recommended for Testing)
```bash
# Run with mock data (realistic GCP costs)
./scripts/run_mock_data.sh
```

### Option 2: Real BigQuery Data (Production)
```bash
# Run with real GCP data
./scripts/run_go_framework.sh
```

### Option 3: Complete System
```bash
# Run everything (mock data + all components)
./scripts/run_complete_system.sh
```

## 🔧 Configuration

### Alert Thresholds
Edit `config/alert_thresholds.json`:
```json
{
  "cost_spike_threshold": 1.0,
  "cost_spike_percentage": 10.0,
  "anomaly_threshold": 2.0
}
```

### Environment Variables
Copy `slack_bot/env_example.txt` to `slack_bot/.env` and configure:
- `SLACK_BOT_TOKEN`
- `SLACK_SIGNING_SECRET`
- `SLACK_APP_TOKEN`

## 📊 System Components

### 1. **Data Sources**
- **Real Data**: Go framework connects to BigQuery
- **Mock Data**: Python generator creates realistic test data

### 2. **AI/ML Pipeline**
- **Anomaly Detection**: Identifies cost spikes and unusual patterns
- **Cost Forecasting**: Predicts future costs using Prophet
- **Semantic Search**: Natural language queries via RAG

### 3. **Alert System**
- **Slack Notifications**: Real-time cost alerts
- **Email Notifications**: Backup alert system
- **Web Dashboard**: Real-time monitoring interface

### 4. **Slack Bot**
- **Natural Language Queries**: Ask about costs in plain English
- **Cost Statistics**: Get detailed cost breakdowns
- **Alert Management**: Configure and manage alerts

## 🎯 Use Cases

### Development/Testing
- Use mock data for rapid development
- Test alert configurations
- Validate AI/ML pipeline

### Production
- Connect to real BigQuery billing data
- Monitor actual GCP costs
- Get real-time alerts for cost spikes

## 📈 Features

- **Real-time Cost Monitoring**: Track daily, MTD, and dimensional costs
- **Anomaly Detection**: AI-powered cost spike detection
- **Cost Forecasting**: Predict future costs with 30-day forecasts
- **Natural Language Queries**: Ask about costs in plain English
- **Slack Integration**: Real-time alerts and queries
- **Web Dashboard**: Real-time monitoring with charts and alerts
- **Alert Management**: Configurable thresholds and notifications

## 🔍 Monitoring

- **Dashboard**: http://localhost:5001
- **Logs**: Check `data/logs/` directory
- **Alerts**: View `data/alert_history.json`
- **Forecasts**: Check `ai_ml/forecasts/` directory

## 🛠️ Troubleshooting

### Common Issues
1. **Port 5000 in use**: Dashboard uses port 5001
2. **SQLite version conflicts**: Chroma DB uses pysqlite3 patch
3. **Slack bot not responding**: Check environment variables and app permissions

### Logs
- Alert System: `data/logs/alert_system.log`
- Dashboard: `data/logs/dashboard.log`
- AI/ML Pipeline: Check console output

## 📝 Development

### Adding New Services
1. Update mock data generator (`mock-data/scripts/mock_data_generator.py`)
2. Add service to Go monitors (`go-framework/vendors/gcp/monitors/`)
3. Update forecasting (`ai_ml/cost_forecasting.py`)

### Custom Alerts
1. Modify alert thresholds in `config/alert_thresholds.json`
2. Add new alert types in `alert_system/alert_manager.py`
3. Test with `tests/force_alert_test.py`
