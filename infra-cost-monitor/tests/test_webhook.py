#!/usr/bin/env python3
"""
Test Slack Webhook
Simple script to test if your Slack webhook is working
"""

import json
import requests
import os

def test_slack_webhook():
    """Test the Slack webhook configuration"""
    
    # Load config
    config_file = "alert_system/config.json"
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    webhook_url = config.get("slack_webhook_url", "")
    
    if not webhook_url or webhook_url == "YOUR_SLACK_WEBHOOK_URL_HERE":
        print("❌ Webhook URL not configured!")
        print("Please update alert_system/config.json with your Slack webhook URL")
        return False
    
    print(f"🔗 Testing webhook: {webhook_url[:50]}...")
    
    # Test message
    test_message = {
        "text": "🧪 Test Alert from GCP Cost Monitor\nThis is a test message to verify your webhook is working!",
        "username": "GCP Cost Monitor",
        "icon_emoji": ":test_tube:"
    }
    
    try:
        response = requests.post(webhook_url, json=test_message, timeout=10)
        
        if response.status_code == 200:
            print("✅ Webhook test successful!")
            print("📱 Check your Slack channel for the test message")
            return True
        else:
            print(f"❌ Webhook test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        return False

if __name__ == "__main__":
    test_slack_webhook() 