#!/usr/bin/env python3
"""
Wrapper script for Slack bot that applies SQLite patch before imports
"""

import sys
import os

# Apply SQLite patch before any other imports
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
    print("Applied SQLite patch using pysqlite3")
except ImportError:
    print("Warning: pysqlite3 not available, using system sqlite3")

# Set environment variables to disable CoreML
os.environ['ONNXRUNTIME_PROVIDER'] = 'CPUExecutionProvider'
os.environ['ONNXRUNTIME_DISABLE_COREML'] = '1'

# Now import and run the Slack bot
if __name__ == "__main__":
    try:
        from slack_bot import main
        main()
    except Exception as e:
        print(f"Error running Slack bot: {e}")
        sys.exit(1) 