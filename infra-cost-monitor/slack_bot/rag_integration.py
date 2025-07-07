# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
RAG Integration for Slack Bot
Connects to existing Chroma database and provides semantic search capabilities
"""

import logging
import re
import threading
import queue
from typing import Dict, List, Any, Optional
import chromadb
from chromadb.config import Settings
import ollama

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGIntegration:
    def __init__(self, chroma_dir: str = "../ai_ml/chroma_db"):
        """
        Initialize RAG integration with existing Chroma database
        
        Args:
            chroma_dir: Path to the Chroma database directory
        """
        self.chroma_dir = chroma_dir
        
        # Initialize Chroma client
        logger.info("Initializing RAG integration with Chroma...")
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=chroma_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get existing collections
            collections = self.chroma_client.list_collections()
            logger.info(f"Found collections: {[col.name for col in collections]}")
            
            # Connect to existing collections
            try:
                self.cost_collection = self.chroma_client.get_collection("cost_data")
                logger.info("Connected to cost_data collection")
            except Exception:
                logger.warning("cost_data collection not found, creating...")
                self.cost_collection = self.chroma_client.create_collection("cost_data")
            
            try:
                self.anomaly_collection = self.chroma_client.get_collection("anomaly_data")
                logger.info("Connected to anomaly_data collection")
            except Exception:
                logger.warning("anomaly_data collection not found, creating...")
                self.anomaly_collection = self.chroma_client.create_collection("anomaly_data")
            
            logger.info("RAG integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG integration: {e}")
            raise
        
        # Initialize Ollama
        try:
            ollama.list()
            logger.info("Connected to Ollama")
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")
            logger.warning("LLM features will be limited")
    
    def search_relevant_data(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant cost data using vector similarity
        
        Args:
            query: User's question
            n_results: Number of results to return
            
        Returns:
            List of relevant documents with metadata
        """
        try:
            logger.info(f"Searching for: {query}")
            
            # Search in both collections
            cost_results = self.cost_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            anomaly_results = self.anomaly_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Combine and format results
            relevant_data = []
            
            if cost_results['documents']:
                for i, doc in enumerate(cost_results['documents'][0]):
                    relevant_data.append({
                        'text': doc,
                        'metadata': cost_results['metadatas'][0][i],
                        'type': 'cost_data',
                        'distance': cost_results['distances'][0][i] if 'distances' in cost_results else None
                    })
            
            if anomaly_results['documents']:
                for i, doc in enumerate(anomaly_results['documents'][0]):
                    relevant_data.append({
                        'text': doc,
                        'metadata': anomaly_results['metadatas'][0][i],
                        'type': 'anomaly',
                        'distance': anomaly_results['distances'][0][i] if 'distances' in anomaly_results else None
                    })
            
            # Sort by relevance (lower distance = more relevant)
            relevant_data.sort(key=lambda x: x.get('distance', 1.0))
            
            logger.info(f"Found {len(relevant_data)} relevant documents")
            return relevant_data
            
        except Exception as e:
            logger.error(f"Error searching data: {e}")
            return []
    
    def generate_fast_response(self, query: str, relevant_data: List[Dict[str, Any]]) -> str:
        """
        Generate fast response without LLM for common questions
        
        Args:
            query: User's question
            relevant_data: Retrieved relevant documents
            
        Returns:
            Formatted response string
        """
        query_lower = query.lower()
        
        # Check for common patterns and provide instant responses
        if any(word in query_lower for word in ['expensive', 'cost', 'high cost', 'most expensive']):
            cost_items = [item for item in relevant_data if item['type'] == 'cost_data']
            if cost_items:
                costs = []
                for item in cost_items:
                    text = item['text']
                    if '₹' in text:
                        cost_match = re.search(r'₹([\d,]+\.?\d*)', text)
                        if cost_match:
                            cost_val = float(cost_match.group(1).replace(',', ''))
                            costs.append((cost_val, text))
                
                if costs:
                    costs.sort(reverse=True)
                    response = "*Most Expensive Services:*\n"
                    for i, (cost, text) in enumerate(costs[:3]):
                        response += f"{i+1}. {text}\n"
                    return response
        
        elif any(word in query_lower for word in ['anomaly', 'anomalies', 'unusual', 'alert']):
            anomaly_items = [item for item in relevant_data if item['type'] == 'anomaly']
            if anomaly_items:
                response = "*Recent Anomalies Detected:*\n"
                for i, item in enumerate(anomaly_items[:3]):
                    response += f"{i+1}. {item['text']}\n"
                return response
        
        elif any(word in query_lower for word in ['trend', 'trends', 'daily', 'month']):
            cost_items = [item for item in relevant_data if item['type'] == 'cost_data']
            if cost_items:
                response = "*Recent Cost Trends:*\n"
                for i, item in enumerate(cost_items[:3]):
                    response += f"{i+1}. {item['text']}\n"
                return response
        
        # If no pattern matches, return a summary
        if relevant_data:
            response = "*Available Data Summary:*\n"
            for i, item in enumerate(relevant_data[:3]):
                response += f"{i+1}. {item['text'][:100]}...\n"
            return response
        
        return "I couldn't find specific data for your question. Try asking about 'expensive services', 'anomalies', or 'cost trends'."
    
    def generate_llm_response(self, query: str, relevant_data: List[Dict[str, Any]], timeout: int = 10) -> str:
        """
        Generate response using Ollama LLM with timeout
        
        Args:
            query: User's question
            relevant_data: Retrieved relevant documents
            timeout: Timeout in seconds
            
        Returns:
            LLM-generated response or fallback response
        """
        try:
            # Prepare context
            context_items = relevant_data[:2]
            context = "\n".join([item['text'] for item in context_items])
            
            # Create prompt
            prompt = f"""GCP Cost Assistant. Context: {context[:300]}... Question: {query}. Provide a brief, helpful response:"""
            
            # Try LLM with timeout
            result_queue = queue.Queue()
            
            def llm_call():
                try:
                    response = ollama.chat(model='llama3.2', messages=[
                        {'role': 'user', 'content': prompt}
                    ])
                    result_queue.put(response['message']['content'])
                except Exception as e:
                    result_queue.put(f"LLM Error: {str(e)}")
            
            # Start LLM in thread
            thread = threading.Thread(target=llm_call)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                return self.generate_fast_response(query, relevant_data) + "\n\n_(LLM response timed out, showing data summary above)_"
            
            llm_result = result_queue.get_nowait()
            if "LLM Error" in llm_result:
                return self.generate_fast_response(query, relevant_data)
            
            return llm_result
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return self.generate_fast_response(query, relevant_data)
    
    def process_query(self, query: str, use_llm: bool = True) -> str:
        """
        Process a user query and return a response
        
        Args:
            query: User's question
            use_llm: Whether to use LLM for complex questions
            
        Returns:
            Formatted response string
        """
        logger.info(f"Processing query: {query}")
        
        # Search for relevant data
        relevant_data = self.search_relevant_data(query)
        
        if not relevant_data:
            return "I couldn't find any relevant cost data for your question. Try asking about 'cost trends', 'anomalies', or 'daily costs'."
        
        # Generate response
        if use_llm and any(word in query.lower() for word in ['why', 'how', 'explain', 'analyze']):
            response = self.generate_llm_response(query, relevant_data)
        else:
            response = self.generate_fast_response(query, relevant_data)
        
        return response
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Chroma collections
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            stats = {}
            
            # Get cost collection stats
            cost_count = self.cost_collection.count()
            stats['cost_data_count'] = cost_count
            
            # Get anomaly collection stats
            anomaly_count = self.anomaly_collection.count()
            stats['anomaly_data_count'] = anomaly_count
            
            stats['total_documents'] = cost_count + anomaly_count
            stats['collections'] = ['cost_data', 'anomaly_data']
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {'error': str(e)} 