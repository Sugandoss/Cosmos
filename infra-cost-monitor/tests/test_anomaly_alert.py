#!/usr/bin/env python3
"""
Test Anomaly Alert
Send a test anomaly alert directly to Slack
"""

import json
import requests
import os

def test_anomaly_alert():
    """Test sending an anomaly alert directly to Slack"""
    
    # Load config
    config_file = "alert_system/config.json"
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    webhook_url = config.get("slack_webhook_url", "")
    
    if not webhook_url:
        print("❌ No webhook URL found in config")
        return False
    
    print(f"🔗 Testing anomaly alert with webhook: {webhook_url[:50]}...")
    
    # Test anomaly alert message
    test_message = {
        "text": "🔍 *Anomaly Detected*\n*Service:* Compute Engine\n*Anomaly Score:* 1.00\n*Cost Impact:* ₹9.34\n*Time:* 2025-07-04T10:56:44",
        "username": "GCP Cost Monitor",
        "icon_emoji": ":warning:"
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=test_message,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Anomaly alert sent successfully!")
            print("📱 Check your Slack channel for the anomaly alert")
            return True
        else:
            print(f"❌ Failed to send anomaly alert. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending anomaly alert: {e}")
        return False

if __name__ == "__main__":
    print("🚨 Test Anomaly Alert")
    print("=" * 30)
    test_anomaly_alert() 