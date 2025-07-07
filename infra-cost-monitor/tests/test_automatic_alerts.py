#!/usr/bin/env python3
"""
Test Automatic Alert System
Demonstrates how anomalies automatically trigger Slack alerts
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add alert system to path
sys.path.append('./alert_system')
from alert_manager import AlertManager, AlertConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_automatic_alerts():
    """Test automatic alert triggering with mock data"""
    
    print("🚨 Testing Automatic Alert System")
    print("=" * 50)
    
    # Load mock anomalies
    anomalies_file = "output/anomalies.json"
    if not os.path.exists(anomalies_file):
        print("❌ No anomalies.json found. Run mock_data_generator.py first.")
        return
    
    with open(anomalies_file, 'r') as f:
        anomalies = json.load(f)
    
    print(f"📊 Found {len(anomalies)} anomalies to test")
    
    # Initialize alert manager
    config_data = {
        "slack_webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
        "email_smtp_server": "smtp.gmail.com",
        "email_smtp_port": 587,
        "email_username": os.getenv("EMAIL_USERNAME", ""),
        "email_password": os.getenv("EMAIL_PASSWORD", ""),
        "email_recipients": [],
        "escalation_recipients": [],
        "alert_cooldown_minutes": 30,
        "max_alerts_per_hour": 10
    }
    
    config = AlertConfig(**config_data)
    alert_manager = AlertManager(config)
    
    print("✅ Alert manager initialized")
    
    # Test each anomaly
    for i, anomaly in enumerate(anomalies):
        print(f"\n🔍 Testing Anomaly {i+1}:")
        print(f"   Service: {anomaly.get('service_desc', 'unknown')}")
        print(f"   Cost Impact: ₹{anomaly.get('cost_impact', 0):.2f}")
        print(f"   Severity: {anomaly.get('severity', 'medium')}")
        
        # Prepare anomaly data
        anomaly_data = {
            'service': anomaly.get('service_desc', 'unknown'),
            'anomaly_score': anomaly.get('percentage_diff', 0) / 100,
            'cost_impact': anomaly.get('cost_impact', 0),
            'description': anomaly.get('description', ''),
            'severity': anomaly.get('severity', 'medium'),
            'timestamp': anomaly.get('timestamp', datetime.now().isoformat())
        }
        
        # Check if alert should be triggered
        alert = alert_manager.check_anomaly(anomaly_data)
        
        if alert:
            print(f"   🚨 ALERT TRIGGERED!")
            print(f"   Alert Type: {alert['type']}")
            print(f"   Severity: {alert['severity']}")
            
            # Send alert
            success = alert_manager.send_alert(alert)
            if success:
                print(f"   ✅ Alert sent successfully to Slack")
            else:
                print(f"   ❌ Failed to send alert")
        else:
            print(f"   ⏭️  No alert triggered (below threshold)")
    
    print(f"\n🎯 Test completed!")
    print(f"📊 Check your Slack channel for alerts")
    print(f"📁 Alert history saved to: alert_system/alert_history.json")

if __name__ == "__main__":
    test_automatic_alerts() 