#!/usr/bin/env python3
"""
Direct Alert Test
Bypasses ChromaDB and directly tests alert system with current anomaly data
"""

import json
import os
import sys
from datetime import datetime

# Add alert system to path
sys.path.append('../alert_system')
from alert_manager import AlertManager, AlertConfig

def test_alerts_direct():
    """Test alerts directly without ChromaDB"""
    
    print("🚨 Direct Alert Test (Bypassing ChromaDB)")
    print("=" * 50)
    
    # Load current anomalies
    anomalies_file = "mock-data/output/anomalies.json"
    if not os.path.exists(anomalies_file):
        print("❌ No anomalies.json found")
        return
    
    with open(anomalies_file, 'r') as f:
        anomalies = json.load(f)
    
    print(f"📊 Found {len(anomalies)} anomalies")
    
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
        print(f"   Raw anomaly: {anomaly}")
        
        # Support both old and new formats
        service = anomaly.get('service_desc') or anomaly.get('service', 'unknown')
        if 'percentage_diff' in anomaly:
            anomaly_score = anomaly.get('percentage_diff', 100) / 100
        elif 'anomaly_score' in anomaly:
            anomaly_score = anomaly.get('anomaly_score', 1.0)
        else:
            anomaly_score = 1.0
        cost_impact = anomaly.get('cost_impact', 0)
        description = anomaly.get('description', '')
        severity = anomaly.get('severity', 'medium')
        timestamp = anomaly.get('timestamp') or anomaly.get('detected_at', '')
        
        print(f"   Service: {service}")
        print(f"   Cost Impact: ₹{cost_impact:.2f}")
        print(f"   Anomaly Score: {anomaly_score:.2f}")
        print(f"   Severity: {severity}")
        
        anomaly_data = {
            'service': service,
            'anomaly_score': anomaly_score,
            'cost_impact': cost_impact,
            'description': description,
            'severity': severity,
            'timestamp': timestamp
        }
        
        # Check if alert should be triggered
        print(f"   🔍 Checking anomaly against thresholds...")
        print(f"   📊 Cost impact: {cost_impact} vs threshold: 1.0")
        print(f"   🎯 Service: '{service}' vs threshold service: 'all'")
        
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
            print(f"   🔍 Debug: anomaly_score={anomaly_score}, cost_impact={cost_impact}")
    
    print(f"\n🎯 Test completed!")
    print(f"📊 Check your Slack channel for alerts")

if __name__ == "__main__":
    test_alerts_direct() 