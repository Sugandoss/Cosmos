#!/usr/bin/env python3
"""
Trigger Alerts Script
Reads anomalies from the mock data and triggers alerts
"""

import json
import os
import sys
import time
from datetime import datetime

# Add the alert_system directory to the path
sys.path.append('alert_system')

from alert_manager import AlertManager, AlertConfig

def load_config():
    """Load alert configuration"""
    config_file = "alert_system/config.json"
    if not os.path.exists(config_file):
        print(f"Config file {config_file} not found")
        return None
    
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    return AlertConfig(**config_data)

def load_anomalies():
    """Load anomalies from the mock data output"""
    anomalies_file = "mock-data/output/anomalies.json"
    if not os.path.exists(anomalies_file):
        print(f"Anomalies file {anomalies_file} not found")
        return []
    
    with open(anomalies_file, 'r') as f:
        anomalies = json.load(f)
    
    return anomalies

def trigger_alerts():
    """Trigger alerts for all anomalies"""
    print("🔔 Triggering alerts for anomalies...")
    
    # Load configuration
    config = load_config()
    if not config:
        print("❌ Failed to load configuration")
        return
    
    # Initialize alert manager
    alert_manager = AlertManager(config)
    
    # Load anomalies
    anomalies = load_anomalies()
    if not anomalies:
        print("❌ No anomalies found")
        return
    
    print(f"📊 Found {len(anomalies)} anomalies to process")
    
    # Process each anomaly
    for i, anomaly in enumerate(anomalies, 1):
        print(f"\n🔍 Processing anomaly {i}/{len(anomalies)}:")
        print(f"   Service: {anomaly['service']}")
        print(f"   Date: {anomaly['date']}")
        print(f"   Cost Impact: ₹{anomaly['cost_impact']:.2f}")
        print(f"   Description: {anomaly['description']}")
        
        # Check if this anomaly should trigger an alert
        alert = alert_manager.check_anomaly(anomaly)
        
        if alert:
            print(f"   ✅ Alert triggered!")
            success = alert_manager.send_alert(alert)
            if success:
                print(f"   📤 Alert sent successfully")
            else:
                print(f"   ❌ Failed to send alert")
        else:
            print(f"   ⚠️  No alert triggered (below threshold)")
        
        # Small delay between processing
        time.sleep(1)
    
    print(f"\n🎉 Finished processing {len(anomalies)} anomalies")

if __name__ == "__main__":
    trigger_alerts() 