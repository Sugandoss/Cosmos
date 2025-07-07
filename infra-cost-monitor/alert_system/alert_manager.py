#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production-Ready Alert Manager
Handles real-time notifications via Slack and Email with escalation policies
"""

import os
import json
import logging
import smtplib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    service: str
    threshold_amount: float
    threshold_percentage: float
    time_window_hours: int
    alert_type: str  # 'cost_spike', 'anomaly', 'budget_exceeded'

@dataclass
class AlertConfig:
    """Alert configuration"""
    slack_webhook_url: str
    email_smtp_server: str
    email_smtp_port: int
    email_username: str
    email_password: str
    email_recipients: List[str]
    escalation_recipients: List[str]
    alert_cooldown_minutes: int = 30
    max_alerts_per_hour: int = 10

class AlertManager:
    """Production-ready alert manager with escalation policies"""
    
    def __init__(self, config: AlertConfig):
        self.config = config
        self.alert_history: List[Dict] = []
        self.last_alert_time: Dict[str, datetime] = {}
        self.alert_count_hourly: Dict[str, int] = {}
        
        # Load alert thresholds
        self.thresholds = self._load_thresholds()
        
        logger.info("Alert Manager initialized")
    
    def _load_thresholds(self) -> List[AlertThreshold]:
        """Load alert thresholds from configuration"""
        default_thresholds = [
            AlertThreshold(
                service="all",
                threshold_amount=100.0,
                threshold_percentage=50.0,
                time_window_hours=24,
                alert_type="cost_spike"
            ),
            AlertThreshold(
                service="all",
                threshold_amount=500.0,
                threshold_percentage=100.0,
                time_window_hours=24,
                alert_type="budget_exceeded"
            ),
            AlertThreshold(
                service="all",
                threshold_amount=50.0,
                threshold_percentage=25.0,
                time_window_hours=1,
                alert_type="anomaly"
            )
        ]
        
        # Load from file if exists
        thresholds_file = "../config/alert_thresholds.json"
        if os.path.exists(thresholds_file):
            try:
                with open(thresholds_file, 'r') as f:
                    data = json.load(f)
                    return [AlertThreshold(**t) for t in data]
            except Exception as e:
                logger.error(f"Error loading thresholds: {e}")
        
        return default_thresholds
    
    def check_cost_spike(self, cost_data: Dict[str, Any]) -> Optional[Dict]:
        """Check for cost spikes and trigger alerts"""
        current_cost = cost_data.get('current_cost', 0)
        previous_cost = cost_data.get('previous_cost', 0)
        service = cost_data.get('service', 'unknown')
        
        if previous_cost == 0:
            return None
        
        cost_increase = current_cost - previous_cost
        cost_increase_percentage = (cost_increase / previous_cost) * 100
        
        for threshold in self.thresholds:
            if (threshold.service == service or threshold.service == "all") and \
               threshold.alert_type == "cost_spike":
                
                if (cost_increase >= threshold.threshold_amount or 
                    cost_increase_percentage >= threshold.threshold_percentage):
                    
                    alert = {
                        'type': 'cost_spike',
                        'service': service,
                        'current_cost': current_cost,
                        'previous_cost': previous_cost,
                        'increase_amount': cost_increase,
                        'increase_percentage': cost_increase_percentage,
                        'threshold_amount': threshold.threshold_amount,
                        'threshold_percentage': threshold.threshold_percentage,
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'high' if cost_increase_percentage > 100 else 'medium'
                    }
                    
                    if self._should_send_alert(alert):
                        return alert
        
        return None
    
    def check_budget_exceeded(self, cost_data: Dict[str, Any]) -> Optional[Dict]:
        """Check if budget has been exceeded"""
        current_cost = cost_data.get('current_cost', 0)
        budget_limit = cost_data.get('budget_limit', float('inf'))
        service = cost_data.get('service', 'unknown')
        
        if current_cost > budget_limit:
            for threshold in self.thresholds:
                if (threshold.service == service or threshold.service == "all") and \
                   threshold.alert_type == "budget_exceeded":
                    
                    alert = {
                        'type': 'budget_exceeded',
                        'service': service,
                        'current_cost': current_cost,
                        'budget_limit': budget_limit,
                        'exceeded_amount': current_cost - budget_limit,
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'critical'
                    }
                    
                    if self._should_send_alert(alert):
                        return alert
        
        return None
    
    def check_anomaly(self, anomaly_data: Dict[str, Any]) -> Optional[Dict]:
        """Check for anomalies and trigger alerts"""
        anomaly_score = anomaly_data.get('anomaly_score', 0)
        service = anomaly_data.get('service', 'unknown')
        cost_impact = anomaly_data.get('cost_impact', 0)
        
        print(f"    🔍 DEBUG: Checking anomaly for service '{service}' with cost_impact {cost_impact}")
        print(f"    🔍 DEBUG: Found {len(self.thresholds)} thresholds")
        
        for threshold in self.thresholds:
            print(f"    🔍 DEBUG: Checking threshold - service: '{threshold.service}', alert_type: '{threshold.alert_type}', threshold_amount: {threshold.threshold_amount}")
            
            if (threshold.service == service or threshold.service == "all") and \
               threshold.alert_type == "anomaly":
                
                print(f"    🔍 DEBUG: Threshold matches! Checking if {cost_impact} >= {threshold.threshold_amount}")
                
                if cost_impact >= threshold.threshold_amount:
                    print(f"    🔍 DEBUG: Cost impact {cost_impact} >= threshold {threshold.threshold_amount} - ALERT SHOULD BE TRIGGERED!")
                    
                    alert = {
                        'type': 'anomaly',
                        'service': service,
                        'anomaly_score': anomaly_score,
                        'cost_impact': cost_impact,
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'high' if anomaly_score > 0.8 else 'medium'
                    }
                    
                    print(f"    🔍 DEBUG: Created alert: {alert}")
                    
                    if self._should_send_alert(alert):
                        print(f"    🔍 DEBUG: Alert should be sent!")
                        return alert
                    else:
                        print(f"    🔍 DEBUG: Alert blocked by cooldown/rate limiting")
                else:
                    print(f"    🔍 DEBUG: Cost impact {cost_impact} < threshold {threshold.threshold_amount} - no alert")
            else:
                print(f"    🔍 DEBUG: Threshold doesn't match - service: '{threshold.service}' vs '{service}', alert_type: '{threshold.alert_type}' vs 'anomaly'")
        
        print(f"    🔍 DEBUG: No alert triggered for this anomaly")
        return None
    
    def _should_send_alert(self, alert: Dict) -> bool:
        """Check if alert should be sent based on cooldown and rate limiting"""
        alert_key = f"{alert['type']}_{alert['service']}"
        now = datetime.now()
        
        # Check cooldown
        if alert_key in self.last_alert_time:
            time_since_last = now - self.last_alert_time[alert_key]
            if time_since_last.total_seconds() < self.config.alert_cooldown_minutes * 60:
                return False
        
        # Check rate limiting
        hour_key = now.strftime("%Y-%m-%d-%H")
        if hour_key not in self.alert_count_hourly:
            self.alert_count_hourly[hour_key] = 0
        
        if self.alert_count_hourly[hour_key] >= self.config.max_alerts_per_hour:
            return False
        
        return True
    
    def send_alert(self, alert: Dict) -> bool:
        """Send alert via configured channels"""
        if not self._should_send_alert(alert):
            return False
        
        # Add delay before sending to prevent rate limiting
        time.sleep(1)
        
        success = True
        
        # Send to Slack
        if self.config.slack_webhook_url:
            try:
                self._send_slack_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {e}")
                success = False
        
        # Send to Email
        if self.config.email_smtp_server:
            try:
                self._send_email_alert(alert)
            except Exception as e:
                logger.error(f"Failed to send email alert: {e}")
                success = False
        
        if success:
            # Save to history
            self.alert_history.append(alert)
            self._save_alert_history()
            
            # Update tracking
            service = alert.get('service', 'unknown')
            self.last_alert_time[service] = datetime.now()
            
            # Update hourly count
            current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
            hour_key = current_hour.isoformat()
            self.alert_count_hourly[hour_key] = self.alert_count_hourly.get(hour_key, 0) + 1
            
            logger.info(f"Alert sent successfully: {alert['type']} for {service}")
        
        return success
    
    def _save_alert_history(self):
        """Save alert history to file"""
        try:
            with open('../data/alert_history.json', 'w') as f:
                json.dump(self.alert_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving alert history: {e}")
    
    def _send_slack_alert(self, alert: Dict):
        """Send alert to Slack"""
        if not self.config.slack_webhook_url:
            return
        
        # Format message based on alert type
        if alert['type'] == 'cost_spike':
            message = self._format_cost_spike_slack_message(alert)
        elif alert['type'] == 'budget_exceeded':
            message = self._format_budget_exceeded_slack_message(alert)
        elif alert['type'] == 'anomaly':
            message = self._format_anomaly_slack_message(alert)
        else:
            message = self._format_generic_slack_message(alert)
        
        # Send to Slack
        payload = {
            "text": message,
            "username": "GCP Cost Monitor",
            "icon_emoji": ":warning:"
        }
        
        try:
            response = requests.post(
                self.config.slack_webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent successfully for {alert['service']}")
            else:
                logger.error(f"Slack webhook failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def _send_email_alert(self, alert: Dict):
        """Send alert via email"""
        if not all([self.config.email_smtp_server, self.config.email_username, 
                   self.config.email_password, self.config.email_recipients]):
            return
        
        # Format email
        subject = f"GCP Cost Alert: {alert['type'].replace('_', ' ').title()}"
        body = self._format_email_message(alert)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.config.email_username
        msg['To'] = ', '.join(self.config.email_recipients)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(self.config.email_smtp_server, self.config.email_smtp_port) as server:
            server.starttls()
            server.login(self.config.email_username, self.config.email_password)
            server.send_message(msg)
        
        logger.info(f"Email alert sent to {len(self.config.email_recipients)} recipients")
    
    def _format_cost_spike_slack_message(self, alert: Dict) -> str:
        """Format cost spike alert for Slack"""
        emoji = "🚨" if alert['severity'] == 'critical' else "⚠️"
        
        return f"""{emoji} *Cost Spike Alert*
*Service:* {alert['service']}
*Current Cost:* ₹{alert['current_cost']:.2f}
*Previous Cost:* ₹{alert['previous_cost']:.2f}
*Increase:* ₹{alert['increase_amount']:.2f} ({alert['increase_percentage']:.1f}%)
*Threshold:* ₹{alert['threshold_amount']:.2f} / {alert['threshold_percentage']:.1f}%
*Time:* {alert['timestamp']}"""
    
    def _format_budget_exceeded_slack_message(self, alert: Dict) -> str:
        """Format budget exceeded alert for Slack"""
        return f"""🚨 *Budget Exceeded Alert*
*Service:* {alert['service']}
*Current Cost:* ₹{alert['current_cost']:.2f}
*Budget Limit:* ₹{alert['budget_limit']:.2f}
*Exceeded By:* ₹{alert['exceeded_amount']:.2f}
*Time:* {alert['timestamp']}"""
    
    def _format_anomaly_slack_message(self, alert: Dict) -> str:
        """Format anomaly alert for Slack"""
        emoji = "🔍" if alert['severity'] == 'medium' else "🚨"
        
        return f"""{emoji} *Anomaly Detected*
*Service:* {alert['service']}
*Anomaly Score:* {alert['anomaly_score']:.2f}
*Cost Impact:* ₹{alert['cost_impact']:.2f}
*Time:* {alert['timestamp']}"""
    
    def _format_generic_slack_message(self, alert: Dict) -> str:
        """Format generic alert for Slack"""
        return f"""⚠️ *Alert: {alert['type'].replace('_', ' ').title()}*
*Service:* {alert['service']}
*Details:* {json.dumps(alert, indent=2)}
*Time:* {alert['timestamp']}"""
    
    def _format_email_message(self, alert: Dict) -> str:
        """Format alert for email"""
        if alert['type'] == 'cost_spike':
            return f"""GCP Cost Spike Alert

Service: {alert['service']}
Current Cost: ₹{alert['current_cost']:.2f}
Previous Cost: ₹{alert['previous_cost']:.2f}
Increase: ₹{alert['increase_amount']:.2f} ({alert['increase_percentage']:.1f}%)
Threshold: ₹{alert['threshold_amount']:.2f} / {alert['threshold_percentage']:.1f}%
Time: {alert['timestamp']}

Please review your GCP costs immediately."""
        
        elif alert['type'] == 'budget_exceeded':
            return f"""GCP Budget Exceeded Alert

Service: {alert['service']}
Current Cost: ₹{alert['current_cost']:.2f}
Budget Limit: ₹{alert['budget_limit']:.2f}
Exceeded By: ₹{alert['exceeded_amount']:.2f}
Time: {alert['timestamp']}

URGENT: Budget limit has been exceeded!"""
        
        elif alert['type'] == 'anomaly':
            return f"""GCP Anomaly Alert

Service: {alert['service']}
Anomaly Score: {alert['anomaly_score']:.2f}
Cost Impact: ₹{alert['cost_impact']:.2f}
Time: {alert['timestamp']}

Anomalous cost pattern detected."""
        
        else:
            return f"""GCP Alert: {alert['type'].replace('_', ' ').title()}

Service: {alert['service']}
Details: {json.dumps(alert, indent=2)}
Time: {alert['timestamp']}"""
    
    def get_alert_history(self, hours: int = 24) -> List[Dict]:
        """Get alert history for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alert_history)
        alerts_24h = len(self.get_alert_history(24))
        alerts_7d = len(self.get_alert_history(24 * 7))
        
        # Count by type
        alert_types = {}
        for alert in self.alert_history:
            alert_type = alert['type']
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'alerts_24h': alerts_24h,
            'alerts_7d': alerts_7d,
            'alert_types': alert_types
        }

def main():
    """Main function to run alert manager"""
    # Load configuration
    config_file = "config.json"
    if not os.path.exists(config_file):
        logger.error(f"Config file {config_file} not found")
        return
    
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    config = AlertConfig(**config_data)
    
    # Initialize alert manager
    alert_manager = AlertManager(config)
    
    logger.info("Alert Manager started")
    logger.info("Monitoring for cost spikes, budget exceedances, and anomalies...")
    
    # Keep running
    try:
        while True:
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Alert Manager stopped")

if __name__ == "__main__":
    main() 