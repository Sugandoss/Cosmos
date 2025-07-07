# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
GCP Cost Monitor Slack Bot
Provides RAG-powered cost monitoring via Slack commands and interactions
"""

import os
import logging
from typing import Dict, Any
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from rag_integration import RAGIntegration

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GCPCostSlackBot:
    def __init__(self):
        """Initialize the Slack bot with RAG integration"""
        # Initialize Slack app
        self.app = App(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
        )
        
        # Initialize RAG integration
        try:
            self.rag = RAGIntegration()
            logger.info("RAG integration initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG integration: {e}")
            self.rag = None
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("GCP Cost Slack Bot initialized")
    
    def _register_handlers(self):
        """Register all Slack event handlers"""
        
        # Handle app mentions
        @self.app.event("app_mention")
        def handle_app_mention(event, say):
            """Handle when the bot is mentioned"""
            try:
                # Extract the query from the mention
                text = event['text']
                # Remove the bot mention (e.g., "<@U123456> ")
                query = ' '.join(text.split()[1:])
                
                if not query.strip():
                    say("👋 Hi! I'm your GCP cost monitoring assistant. Ask me about your infrastructure costs!")
                    return
                
                # Process the query
                response = self._process_query(query)
                say(response)
                
            except Exception as e:
                logger.error(f"Error handling app mention: {e}")
                say("Sorry, I encountered an error processing your request. Please try again.")
        
        # Handle direct messages
        @self.app.event("message")
        def handle_direct_message(event, say):
            """Handle direct messages to the bot"""
            try:
                # Only respond to direct messages (not in channels)
                if event.get('channel_type') == 'im':
                    query = event['text'].strip()
                    
                    if not query:
                        say("👋 Hi! I'm your GCP cost monitoring assistant. Ask me about your infrastructure costs!")
                        return
                    
                    # Process the query
                    response = self._process_query(query)
                    say(response)
                    
            except Exception as e:
                logger.error(f"Error handling direct message: {e}")
                say("Sorry, I encountered an error processing your request. Please try again.")
        
        # Handle slash commands
        @self.app.command("/cost-query")
        def handle_cost_query(ack, command, respond):
            """Handle /cost-query slash command"""
            ack()
            
            try:
                query = command['text'].strip()
                
                if not query:
                    respond("Please provide a question. Example: `/cost-query Which services are most expensive?`")
                    return
                
                # Process the query
                response = self._process_query(query)
                respond(response)
                
            except Exception as e:
                logger.error(f"Error handling cost query: {e}")
                respond("Sorry, I encountered an error processing your request. Please try again.")
        
        @self.app.command("/cost-stats")
        def handle_cost_stats(ack, respond):
            """Handle /cost-stats slash command"""
            ack()
            
            try:
                if not self.rag:
                    respond("❌ RAG system not available")
                    return
                
                stats = self.rag.get_collection_stats()
                
                if 'error' in stats:
                    respond(f"❌ Error getting stats: {stats['error']}")
                    return
                
                response = f"""📊 *Cost Data Statistics:*
• Total Documents: {stats['total_documents']}
• Cost Data Records: {stats['cost_data_count']}
• Anomaly Records: {stats['anomaly_data_count']}
• Collections: {', '.join(stats['collections'])}"""
                
                respond(response)
                
            except Exception as e:
                logger.error(f"Error handling cost stats: {e}")
                respond("Sorry, I encountered an error getting statistics.")
        
        @self.app.command("/cost-help")
        def handle_help(ack, respond):
            """Handle /cost-help slash command"""
            ack()
            
            help_text = """🤖 *GCP Cost Monitor Bot Help*

*Commands:*
• `/cost-query <question>` - Ask about your costs
• `/cost-stats` - Get data statistics
• `/cost-help` - Show this help

*Example Questions:*
• "Which services are most expensive?"
• "Show me recent anomalies"
• "What are the cost trends?"
• "How much did we spend yesterday?"
• "Which projects have the highest costs?"

*Features:*
• Real-time cost data analysis
• Anomaly detection insights
• Trend analysis
• Service-level breakdowns

*Tips:*
• Be specific in your questions
• Ask about specific services, projects, or time periods
• Use natural language - I understand context!"""
            
            respond(help_text)
    
    def _process_query(self, query: str) -> str:
        """
        Process a user query using RAG system
        
        Args:
            query: User's question
            
        Returns:
            Formatted response string
        """
        if not self.rag:
            return "❌ RAG system not available. Please check the configuration."
        
        try:
            # Process the query
            response = self.rag.process_query(query)
            
            # Format for Slack (convert markdown to Slack format)
            response = self._format_for_slack(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "Sorry, I encountered an error processing your request. Please try again."
    
    def _format_for_slack(self, text: str) -> str:
        """
        Format response text for Slack
        
        Args:
            text: Raw response text
            
        Returns:
            Slack-formatted text
        """
        # Convert markdown to Slack format
        formatted = text
        
        # Bold text
        formatted = formatted.replace('**', '*')
        
        # Lists
        formatted = formatted.replace('\n• ', '\n• ')
        formatted = formatted.replace('\n1. ', '\n1. ')
        formatted = formatted.replace('\n2. ', '\n2. ')
        formatted = formatted.replace('\n3. ', '\n3. ')
        
        # Code blocks
        formatted = formatted.replace('`', '`')
        
        return formatted
    
    def start(self):
        """Start the Slack bot"""
        if not os.environ.get("SLACK_BOT_TOKEN"):
            logger.error("SLACK_BOT_TOKEN not found in environment variables")
            return
        
        if not os.environ.get("SLACK_SIGNING_SECRET"):
            logger.error("SLACK_SIGNING_SECRET not found in environment variables")
            return
        
        logger.info("Starting GCP Cost Slack Bot...")
        logger.info("Bot will respond to:")
        logger.info("  • App mentions (@bot)")
        logger.info("  • Direct messages")
        logger.info("  • /cost-query command")
        logger.info("  • /cost-stats command")
        logger.info("  • /cost-help command")
        
        # Start the bot
        handler = SocketModeHandler(self.app, os.environ.get("SLACK_APP_TOKEN"))
        handler.start()

def main():
    """Main function to run the Slack bot"""
    bot = GCPCostSlackBot()
    bot.start()

if __name__ == "__main__":
    main() 