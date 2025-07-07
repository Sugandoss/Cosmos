#!/usr/bin/env python3
"""
Test Multiple Alerts
Send multiple anomaly alerts to test the improved delay system
"""

import json
import time
from alert_system.alert_manager import AlertManager, AlertConfig

def test_multiple_alerts():
    """Test sending multiple alerts with delays"""
    
    # Load config
    config_file = "alert_system/config.json"
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    config = AlertConfig(**config_data)
    alert_manager = AlertManager(config)
    
    print("🚨 Test Multiple Alerts")
    print("=" * 40)
    print("Sending 8 anomaly alerts with 1-second delays...")
    print()
    
    # Test anomaly alerts
    test_anomalies = [
        {"service": "Compute Engine", "anomaly_score": 1.0, "cost_impact": 9.34},
        {"service": "BigQuery", "anomaly_score": 1.0, "cost_impact": 7.96},
        {"service": "Cloud SQL", "anomaly_score": 1.0, "cost_impact": 4.62},
        {"service": "Kubernetes Engine", "anomaly_score": 1.0, "cost_impact": 11.48},
        {"service": "Cloud Functions", "anomaly_score": 1.0, "cost_impact": 2.51},
        {"service": "Cloud Storage", "anomaly_score": 1.0, "cost_impact": 1.75},
        {"service": "Pub/Sub", "anomaly_score": 1.0, "cost_impact": 2.76},
        {"service": "Cloud Run", "anomaly_score": 1.0, "cost_impact": 2.65}
    ]
    
    for i, anomaly in enumerate(test_anomalies, 1):
        print(f"📤 Sending alert {i}/8 for {anomaly['service']}...")
        
        alert = alert_manager.check_anomaly(anomaly)
        if alert:
            success = alert_manager.send_alert(alert)
            if success:
                print(f"✅ Alert {i} sent successfully")
            else:
                print(f"❌ Alert {i} failed to send")
        else:
            print(f"⚠️ Alert {i} not triggered (threshold not met)")
        
        print()
    
    print("🎯 Test completed!")
    print("📱 Check your Slack channel for all 8 alerts")
    print("⏱️ Each alert should have a 1-second delay between them")

if __name__ == "__main__":
    test_multiple_alerts() 