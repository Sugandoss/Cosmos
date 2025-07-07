#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wrapper script to run Slack bot with SQLite patch
"""

# Disable CoreML to fix ONNX Runtime issues on macOS
import os
os.environ['ONNXRUNTIME_PROVIDER'] = 'CPUExecutionProvider'

import sys

# Apply SQLite patch first
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
    print("✅ Using pysqlite3 with SQLite 3.50.1")
except ImportError:
    print("❌ pysqlite3 not available, using system sqlite3")
    print("⚠️  You may need to run the AI/ML pipeline first to ensure compatibility")

# Now run the Slack bot
if __name__ == "__main__":
    try:
        print("🤖 Starting GCP Cost Slack Bot...")
        print("📋 Make sure you have:")
        print("   • .env file with Slack tokens")
        print("   • AI/ML pipeline run first (for Chroma DB)")
        print("   • Ollama running (ollama serve)")
        print()
        
        import slack_bot
        slack_bot.main()
    except Exception as e:
        print(f"❌ Error running Slack bot: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you have a .env file with your Slack tokens")
        print("2. Check that your Slack app is properly configured")
        print("3. Run AI/ML pipeline first: cd ../ai_ml && ./run_ai_pipeline.sh")
        print("4. Ensure Ollama is running: ollama serve")
        print("5. Install pysqlite3: pip3 install pysqlite3-binary") 