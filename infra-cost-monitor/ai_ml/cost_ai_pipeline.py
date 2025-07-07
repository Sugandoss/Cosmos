# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
GCP Cost AI/ML Pipeline
Converts structured cost/anomaly data into text summaries and vector embeddings
Uses MiniLM for efficient semantic search
Stores data in Chroma vector database (optional)
Automatically triggers alerts when anomalies are detected
Includes cost forecasting using Prophet
"""

import json
import os
import logging
import sys
from typing import Dict, List, Any
from sentence_transformers import SentenceTransformer

# Add alert system to path
sys.path.append('../alert_system')
from alert_manager import AlertManager, AlertConfig

# Add forecasts to path
sys.path.append('./forecasts')
from cost_forecasting import CostForecaster

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Chroma, but make it optional
CHROMA_AVAILABLE = False
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except (ImportError, RuntimeError) as e:
    logger.warning(f"Chroma not available: {e}")
    CHROMA_AVAILABLE = False

CHROMA_IMPORTED = CHROMA_AVAILABLE

class CustomEmbeddingFunction:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def __call__(self, input):
        # Handle both single strings and lists of strings
        if isinstance(input, str):
            texts = [input]
        else:
            texts = input
        
        # Generate embeddings
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        
        # Return as list of lists
        if isinstance(input, str):
            return embeddings.tolist()
        else:
            return embeddings.tolist()

class CostAIPipeline:
    def __init__(self, output_dir: str = "../output", chroma_dir: str = "./chroma_db"):
        """
        Initialize the AI/ML pipeline
        
        Args:
            output_dir: Directory containing JSON files from Go framework
            chroma_dir: Directory for Chroma vector database
        """
        self.output_dir = output_dir
        self.chroma_dir = chroma_dir
        
        # Initialize embedding model (MiniLM for efficiency)
        logger.info("Loading sentence transformer model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self._chroma_available = CHROMA_IMPORTED
        # Initialize Chroma client with custom embedding function (if available)
        if self._chroma_available:
            try:
                self.chroma_client = chromadb.PersistentClient(path=chroma_dir)
                
                # Create collections with custom embedding function
                embedding_function = CustomEmbeddingFunction()
                
                self.cost_collection = self.chroma_client.get_or_create_collection(
                    name="cost_data",
                    embedding_function=embedding_function
                )
                
                self.anomaly_collection = self.chroma_client.get_or_create_collection(
                    name="anomaly_data", 
                    embedding_function=embedding_function
                )
                logger.info(f"Chroma vector database initialized at {chroma_dir}")
            except Exception as e:
                logger.warning(f"Failed to initialize Chroma: {e}")
                self._chroma_available = False
        else:
            logger.warning("Chroma vector database is not available. Skipping Chroma initialization.")
        
        # Initialize alert manager for automatic alerts
        self.alert_manager = self._initialize_alert_manager()
        
        # Initialize cost forecaster
        self.forecaster = CostForecaster(output_dir=output_dir, forecasts_dir="./forecasts")
        
        logger.info("AI/ML Pipeline initialized successfully")
    
    def _initialize_alert_manager(self) -> AlertManager:
        """Initialize alert manager with configuration"""
        try:
            # Load config from file or use defaults
            config_file = "../alert_system/config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
            else:
                # Default configuration
                config_data = {
                    "slack_webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
                    "email_smtp_server": "smtp.gmail.com",
                    "email_smtp_port": 587,
                    "email_username": os.getenv("EMAIL_USERNAME", ""),
                    "email_password": os.getenv("EMAIL_PASSWORD", ""),
                    "email_recipients": [],
                    "escalation_recipients": [],
                    "alert_cooldown_minutes": 30,
                    "max_alerts_per_hour": 10
                }
            
            config = AlertConfig(**config_data)
            alert_manager = AlertManager(config)
            logger.info("Alert manager initialized successfully")
            return alert_manager
            
        except Exception as e:
            logger.warning(f"Could not initialize alert manager: {e}")
            return None
    
    def load_json_data(self) -> Dict[str, Any]:
        """Load all JSON files from the output directory"""
        data = {}
        
        json_files = {
            'summary': 'summary.json',
            'anomalies': 'anomalies.json',
            'mtd_data': 'mtd_data.json',
            'daily_total_data': 'daily_total_data.json',
            'composite_data': 'composite_data.json'
        }
        
        for key, filename in json_files.items():
            filepath = os.path.join(self.output_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        data[key] = json.load(f)
                    logger.info(f"Loaded {filename}")
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")
            else:
                logger.warning(f"File not found: {filepath}")
        
        return data
    
    def create_cost_summaries(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create human-readable summaries from cost data"""
        summaries = []
        
        # Summary statistics
        if 'summary' in data:
            summary = data['summary']
            summaries.append({
                'text': f"Cost monitoring summary: {summary.get('total_anomalies', 0)} anomalies detected with total cost impact of ₹{summary.get('total_cost_impact', 0):.2f}. Current month cost: ₹{summary.get('current_month_cost', 0):.2f} over {summary.get('current_month_days', 0)} days.",
                'metadata': {
                    'type': 'summary',
                    'total_anomalies': summary.get('total_anomalies', 0),
                    'total_cost_impact': summary.get('total_cost_impact', 0),
                    'current_month_cost': summary.get('current_month_cost', 0)
                }
            })
        
        # MTD data summaries
        if 'mtd_data' in data:
            for mtd in data['mtd_data']:
                summaries.append({
                    'text': f"Month-to-date cost for {mtd['month']}: ₹{mtd['cost']:.2f} over {mtd['days']} days.",
                    'metadata': {
                        'type': 'mtd_data',
                        'month': mtd['month'],
                        'cost': mtd['cost'],
                        'days': mtd['days']
                    }
                })
        
        # Daily cost summaries
        if 'daily_total_data' in data:
            for daily in data['daily_total_data'][-10:]:  # Last 10 days
                summaries.append({
                    'text': f"Daily total cost for {daily['date']}: ₹{daily['cost']:.2f}.",
                    'metadata': {
                        'type': 'daily_total_data',
                        'date': daily['date'],
                        'cost': daily['cost']
                    }
                })
        
        # Composite data summaries
        if 'composite_data' in data:
            for composite in data['composite_data'][-20:]:  # Last 20 records
                summaries.append({
                    'text': f"Composite cost: {composite['service_desc']} - {composite['sku_desc']} in {composite['project_id']} ({composite['region']}) on {composite['date']}: ₹{composite['cost']:.2f}.",
                    'metadata': {
                        'type': 'composite_data',
                        'service_desc': composite['service_desc'],
                        'sku_desc': composite['sku_desc'],
                        'project_id': composite['project_id'],
                        'region': composite['region'],
                        'date': composite['date'],
                        'cost': composite['cost']
                    }
                })
        
        return summaries
    
    def create_anomaly_summaries(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create detailed summaries for anomalies"""
        summaries = []
        
        if 'anomalies' in data and data['anomalies'] is not None:
            for i, anomaly in enumerate(data['anomalies']):
                summary = {
                    'text': f"Anomaly {i+1}: {anomaly.get('test_name', 'Anomaly')}. {anomaly.get('description', 'No description')} Cost impact: ₹{anomaly.get('cost_impact', 0):.2f} with {anomaly.get('percentage_diff', anomaly.get('anomaly_score', 0)*100):.1f}% difference. Severity: {anomaly.get('severity', 'medium')}.",
                    'metadata': {
                        'type': 'anomaly',
                        'test_name': anomaly.get('test_name', ''),
                        'description': anomaly.get('description', ''),
                        'cost_impact': anomaly.get('cost_impact', 0),
                        'percentage_diff': anomaly.get('percentage_diff', anomaly.get('anomaly_score', 0)*100),
                        'severity': anomaly.get('severity', 'medium'),
                        'timestamp': anomaly.get('timestamp', ''),
                        'composite_key': anomaly.get('composite_key', ''),
                        'service': anomaly.get('service', anomaly.get('service_desc', 'unknown'))
                    }
                }
                summaries.append(summary)
        
        return summaries
    
    def store_in_chroma(self, cost_summaries: List[Dict], anomaly_summaries: List[Dict]):
        """Store summaries in Chroma vector database"""
        if not self._chroma_available:
            logger.warning("Chroma vector database is not available. Skipping storage.")
            return

        logger.info("Storing data in Chroma vector database...")
        
        # Store cost data
        if cost_summaries:
            texts = [s['text'] for s in cost_summaries]
            metadatas = [s['metadata'] for s in cost_summaries]
            ids = [f"cost_{i}" for i in range(len(cost_summaries))]
            
            self.cost_collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Stored {len(cost_summaries)} cost summaries")
        
        # Store anomalies
        if anomaly_summaries:
            texts = [s['text'] for s in anomaly_summaries]
            metadatas = [s['metadata'] for s in anomaly_summaries]
            ids = [f"anomaly_{i}" for i in range(len(anomaly_summaries))]
            
            self.anomaly_collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Stored {len(anomaly_summaries)} anomaly summaries")
    
    def run_pipeline(self):
        """Run the complete AI/ML pipeline"""
        logger.info("Starting AI/ML pipeline...")
        
        # Load JSON data
        data = self.load_json_data()
        if not data:
            logger.error("No data found in output directory")
            return
        
        # Create summaries
        cost_summaries = self.create_cost_summaries(data)
        anomaly_summaries = self.create_anomaly_summaries(data)
        
        logger.info(f"Created {len(cost_summaries)} cost summaries and {len(anomaly_summaries)} anomaly summaries")
        
        # Store in Chroma
        self.store_in_chroma(cost_summaries, anomaly_summaries)
        
        # Check for anomalies and trigger alerts
        self._check_and_trigger_alerts(data)
        
        # Run cost forecasting using full year of data
        logger.info("Starting cost forecasting with 1 year of historical data...")
        try:
            forecast_results = self.forecaster.run_all_forecasts(forecast_days=30)
            if forecast_results['total_cost_forecast']:
                logger.info(f"✅ Forecasting completed! Generated forecasts for {forecast_results['summary']['total_services_forecasted']} services")
                logger.info(f"   - Total forecast value: ₹{forecast_results['summary']['total_forecast_value']:.2f}")
                logger.info(f"   - Forecast period: {forecast_results['summary']['forecast_days']} days")
            else:
                logger.warning("⚠️ No forecasting data available")
        except Exception as e:
            logger.error(f"❌ Forecasting failed: {e}")
        
        logger.info("AI/ML pipeline completed successfully!")
        
        return {
            'cost_summaries': len(cost_summaries),
            'anomaly_summaries': len(anomaly_summaries),
            'total_documents': len(cost_summaries) + len(anomaly_summaries)
        }
    
    def _check_and_trigger_alerts(self, data: Dict[str, Any]):
        """Check for anomalies and trigger automatic alerts"""
        if not self.alert_manager:
            logger.warning("Alert manager not available - skipping automatic alerts")
            return
        
        logger.info("Checking for anomalies and triggering alerts...")
        
        # Check anomalies
        if 'anomalies' in data and data['anomalies']:
            for anomaly in data['anomalies']:
                # Support both old and new formats
                service = anomaly.get('service_desc') or anomaly.get('service', 'unknown')
                # Use percentage_diff if present, else anomaly_score, else default to 1.0
                if 'percentage_diff' in anomaly:
                    anomaly_score = anomaly.get('percentage_diff', 100) / 100
                elif 'anomaly_score' in anomaly:
                    anomaly_score = anomaly.get('anomaly_score', 1.0)
                else:
                    anomaly_score = 1.0
                cost_impact = anomaly.get('cost_impact', 0)
                description = anomaly.get('description', '')
                severity = anomaly.get('severity', 'medium')
                timestamp = anomaly.get('timestamp') or anomaly.get('detected_at', '')
                
                anomaly_data = {
                    'service': service,
                    'anomaly_score': anomaly_score,
                    'cost_impact': cost_impact,
                    'description': description,
                    'severity': severity,
                    'timestamp': timestamp
                }
                
                # Check if this anomaly should trigger an alert
                alert = self.alert_manager.check_anomaly(anomaly_data)
                if alert:
                    logger.info(f"Triggering alert for anomaly: {anomaly_data['service']} - ₹{anomaly_data['cost_impact']:.2f}")
                    success = self.alert_manager.send_alert(alert)
                    if success:
                        logger.info(f"✅ Alert sent successfully for {anomaly_data['service']}")
                    else:
                        logger.error(f"❌ Failed to send alert for {anomaly_data['service']}")
                else:
                    logger.info(f"No alert triggered for {anomaly_data['service']} (below threshold)")
        
        # Check for cost spikes in daily data
        if 'daily_total_data' in data and len(data['daily_total_data']) >= 2:
            recent_daily = data['daily_total_data'][-2:]  # Last 2 days
            if len(recent_daily) == 2:
                current_cost = recent_daily[1]['cost']
                previous_cost = recent_daily[0]['cost']
                
                cost_data = {
                    'current_cost': current_cost,
                    'previous_cost': previous_cost,
                    'service': 'daily_total'
                }
                
                alert = self.alert_manager.check_cost_spike(cost_data)
                if alert:
                    logger.info(f"Triggering cost spike alert: ₹{current_cost:.2f} vs ₹{previous_cost:.2f}")
                    success = self.alert_manager.send_alert(alert)
                    if success:
                        logger.info("✅ Cost spike alert sent successfully")
                    else:
                        logger.error("❌ Failed to send cost spike alert")

def main():
    """Main function to run the pipeline"""
    pipeline = CostAIPipeline()
    results = pipeline.run_pipeline()
    
    if results:
        print(f"✅ Pipeline completed!")
        print(f"   - Cost summaries: {results['cost_summaries']}")
        print(f"   - Anomaly summaries: {results['anomaly_summaries']}")
        print(f"   - Total documents: {results['total_documents']}")
        if pipeline._chroma_available:
            print(f"   - Vector DB location: ./chroma_db/")
        print(f"   - Forecasts location: ./forecasts/")
        print(f"   - Using 1 year of historical data for forecasting")

if __name__ == "__main__":
    main() 