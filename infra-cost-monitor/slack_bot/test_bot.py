#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify Slack bot configuration
"""

import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables
load_dotenv()

def test_slack_connection():
    """Test Slack API connection"""
    print("🔍 Testing Slack Bot Configuration...")
    print()
    
    # Check environment variables
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    signing_secret = os.environ.get("SLACK_SIGNING_SECRET")
    app_token = os.environ.get("SLACK_APP_TOKEN")
    
    print("📋 Environment Variables:")
    print(f"   SLACK_BOT_TOKEN: {'✅ Set' if bot_token else '❌ Missing'}")
    print(f"   SLACK_SIGNING_SECRET: {'✅ Set' if signing_secret else '❌ Missing'}")
    print(f"   SLACK_APP_TOKEN: {'✅ Set' if app_token else '❌ Missing'}")
    print()
    
    if not bot_token:
        print("❌ SLACK_BOT_TOKEN not found!")
        return False
    
    # Test API connection
    try:
        client = WebClient(token=bot_token)
        response = client.auth_test()
        
        print("✅ Slack API Connection Successful!")
        print(f"   Bot Name: {response['user']}")
        print(f"   Team: {response['team']}")
        print(f"   User ID: {response['user_id']}")
        print(f"   Team ID: {response['team_id']}")
        print()
        
        # Test bot info
        bot_info = client.users_info(user=response['user_id'])
        print("🤖 Bot Information:")
        print(f"   Display Name: {bot_info['user']['profile']['display_name']}")
        print(f"   Real Name: {bot_info['user']['profile']['real_name']}")
        print(f"   Status: {'✅ Active' if bot_info['user']['deleted'] == False else '❌ Deleted'}")
        print()
        
        return True
        
    except SlackApiError as e:
        print(f"❌ Slack API Error: {e.response['error']}")
        return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def check_app_permissions():
    """Check if app has required permissions"""
    print("🔐 Checking App Permissions...")
    print()
    print("Make sure your Slack app has these scopes:")
    print("   ✅ app_mentions:read")
    print("   ✅ chat:write")
    print("   ✅ commands")
    print("   ✅ im:history")
    print("   ✅ im:read")
    print("   ✅ im:write")
    print()
    print("And these features enabled:")
    print("   ✅ Socket Mode")
    print("   ✅ Event Subscriptions")
    print("   ✅ Slash Commands")
    print()

if __name__ == "__main__":
    if test_slack_connection():
        print("🎉 Bot configuration looks good!")
        print()
        print("📝 Next steps:")
        print("1. Make sure your app is installed to workspace")
        print("2. Try mentioning the bot: @YourBotName hello")
        print("3. Try direct message to the bot")
        print("4. Try slash command: /cost-query hello")
    else:
        print("❌ Bot configuration has issues!")
        print()
        check_app_permissions() 