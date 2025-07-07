#!/usr/bin/env python3
"""
Force Alert Test
Test if Slack webhook is working by sending a test alert
"""

import json
import requests
import os

def test_slack_webhook():
    """Test Slack webhook directly"""
    
    # Load config
    config_file = "alert_system/config.json"
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    webhook_url = config.get("slack_webhook_url", "")
    
    if not webhook_url:
        print("❌ No webhook URL found in config")
        return False
    
    print(f"🔗 Testing webhook: {webhook_url[:50]}...")
    
    # Test message
    test_message = {
        "text": "🧪 FORCE TEST: This is a test alert from GCP Cost Monitor\n\nThis should appear in your Slack channel if the webhook is working correctly.",
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
            print("✅ Test message sent successfully!")
            print("📱 Check your Slack channel for the test message")
            return True
        else:
            print(f"❌ Failed to send message. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

if __name__ == "__main__":
    print("🚨 Force Alert Test")
    print("=" * 30)
    test_slack_webhook() 