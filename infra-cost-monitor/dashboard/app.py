#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GCP Cost Monitor Dashboard
Real-time web dashboard for cost monitoring and alert management
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
socketio = SocketIO(app, cors_allowed_origins="*")

class DashboardData:
    """Manages dashboard data and real-time updates"""
    
    def __init__(self):
        self.cost_data = []
        self.anomaly_data = []
        self.alert_data = []
        self.last_update = datetime.now()
        self.update_interval = 30  # seconds
        
        # Start background update thread
        self.running = True
        self.update_thread = threading.Thread(target=self._background_update)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def _background_update(self):
        """Background thread to update data periodically"""
        while self.running:
            try:
                self._load_latest_data()
                self._broadcast_updates()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in background update: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _load_latest_data(self):
        """Load latest data from JSON files"""
        try:
            # Load cost data
            cost_file = "../output/composite_data.json"
            if os.path.exists(cost_file):
                with open(cost_file, 'r') as f:
                    self.cost_data = json.load(f)
            
            # Load anomaly data
            anomaly_file = "../output/anomalies.json"
            if os.path.exists(anomaly_file):
                with open(anomaly_file, 'r') as f:
                    self.anomaly_data = json.load(f)
            
            # Load alert data
            alert_file = "../alert_system/alert_history.json"
            if os.path.exists(alert_file):
                with open(alert_file, 'r') as f:
                    self.alert_data = json.load(f)
            
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
    
    def _broadcast_updates(self):
        """Broadcast updates to connected clients"""
        try:
            socketio.emit('data_update', {
                'cost_data': self.cost_data,
                'anomaly_data': self.anomaly_data,
                'alert_data': self.alert_data,
                'last_update': self.last_update.isoformat()
            })
        except Exception as e:
            logger.error(f"Error broadcasting updates: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return {
            'cost_data': self.cost_data,
            'anomaly_data': self.anomaly_data,
            'alert_data': self.alert_data,
            'last_update': self.last_update.isoformat()
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary statistics"""
        if not self.cost_data:
            return {}
        
        total_cost = sum(item.get('cost', 0) for item in self.cost_data)
        services = {}
        
        for item in self.cost_data:
            service = item.get('service', 'Unknown')
            cost = item.get('cost', 0)
            services[service] = services.get(service, 0) + cost
        
        return {
            'total_cost': total_cost,
            'services': services,
            'data_points': len(self.cost_data)
        }
    
    def get_anomaly_summary(self) -> Dict[str, Any]:
        """Get anomaly summary statistics"""
        if not self.anomaly_data:
            return {}
        
        total_anomalies = len(self.anomaly_data)
        high_severity = len([a for a in self.anomaly_data if a.get('severity') == 'high'])
        medium_severity = len([a for a in self.anomaly_data if a.get('severity') == 'medium'])
        
        return {
            'total_anomalies': total_anomalies,
            'high_severity': high_severity,
            'medium_severity': medium_severity
        }
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        if not self.alert_data:
            return {}
        
        total_alerts = len(self.alert_data)
        critical_alerts = len([a for a in self.alert_data if a.get('severity') == 'critical'])
        high_alerts = len([a for a in self.alert_data if a.get('severity') == 'high'])
        
        return {
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts,
            'high_alerts': high_alerts
        }

# Initialize dashboard data
dashboard_data = DashboardData()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    """API endpoint to get dashboard data"""
    return jsonify(dashboard_data.get_dashboard_data())

@app.route('/api/summary')
def get_summary():
    """API endpoint to get summary statistics"""
    return jsonify({
        'cost_summary': dashboard_data.get_cost_summary(),
        'anomaly_summary': dashboard_data.get_anomaly_summary(),
        'alert_summary': dashboard_data.get_alert_summary()
    })

@app.route('/api/cost-trends')
def get_cost_trends():
    """API endpoint to get cost trends"""
    if not dashboard_data.cost_data:
        return jsonify([])
    
    # Group by date and calculate daily totals
    daily_costs = {}
    for item in dashboard_data.cost_data:
        date = item.get('date', '')
        cost = item.get('cost', 0)
        daily_costs[date] = daily_costs.get(date, 0) + cost
    
    # Convert to sorted list
    trends = [{'date': date, 'cost': cost} for date, cost in daily_costs.items()]
    trends.sort(key=lambda x: x['date'])
    
    return jsonify(trends)

@app.route('/api/service-breakdown')
def get_service_breakdown():
    """API endpoint to get service cost breakdown"""
    if not dashboard_data.cost_data:
        return jsonify([])
    
    service_costs = {}
    for item in dashboard_data.cost_data:
        service = item.get('service', 'Unknown')
        cost = item.get('cost', 0)
        service_costs[service] = service_costs.get(service, 0) + cost
    
    breakdown = [{'service': service, 'cost': cost} for service, cost in service_costs.items()]
    breakdown.sort(key=lambda x: x['cost'], reverse=True)
    
    return jsonify(breakdown)

@app.route('/api/recent-alerts')
def get_recent_alerts():
    """API endpoint to get recent alerts"""
    if not dashboard_data.alert_data:
        return jsonify([])
    
    # Get alerts from last 24 hours
    cutoff_time = datetime.now() - timedelta(hours=24)
    recent_alerts = []
    
    for alert in dashboard_data.alert_data:
        alert_time = datetime.fromisoformat(alert.get('timestamp', ''))
        if alert_time > cutoff_time:
            recent_alerts.append(alert)
    
    # Sort by timestamp (newest first)
    recent_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return jsonify(recent_alerts[:10])  # Return last 10 alerts

@app.route('/api/anomalies')
def get_anomalies():
    """API endpoint to get recent anomalies"""
    if not dashboard_data.anomaly_data:
        return jsonify([])
    
    # Sort by timestamp (newest first)
    anomalies = sorted(dashboard_data.anomaly_data, 
                      key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return jsonify(anomalies[:20])  # Return last 20 anomalies

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected to dashboard")
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected from dashboard")

@socketio.on('request_data')
def handle_data_request():
    """Handle data request from client"""
    emit('data_update', dashboard_data.get_dashboard_data())

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data_last_update': dashboard_data.last_update.isoformat()
    })

def create_dashboard_templates():
    """Create dashboard HTML template"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(template_dir, exist_ok=True)
    
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GCP Cost Monitor Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.socket.io/4.0.1/socket.io.min.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        .card:hover {
            transform: translateY(-2px);
        }
        .card h3 {
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .alert-item {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0;
        }
        .alert-critical {
            background: #f8d7da;
            border-color: #f5c6cb;
        }
        .alert-high {
            background: #fff3cd;
            border-color: #ffeaa7;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .status-online {
            background-color: #28a745;
        }
        .status-offline {
            background-color: #dc3545;
        }
        .refresh-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 0;
        }
        .refresh-button:hover {
            background: #5a6fd8;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 GCP Cost Monitor Dashboard</h1>
        <p>Real-time cost monitoring and alert management</p>
        <div>
            <span class="status-indicator status-online" id="status-indicator"></span>
            <span id="status-text">Connected</span>
            <span id="last-update"></span>
        </div>
    </div>

    <div class="dashboard-grid">
        <div class="card">
            <h3>💰 Cost Summary</h3>
            <div class="metric">
                <span>Total Cost:</span>
                <span class="metric-value" id="total-cost">₹0.00</span>
            </div>
            <div class="metric">
                <span>Data Points:</span>
                <span class="metric-value" id="data-points">0</span>
            </div>
        </div>

        <div class="card">
            <h3>🚨 Anomalies</h3>
            <div class="metric">
                <span>Total Anomalies:</span>
                <span class="metric-value" id="total-anomalies">0</span>
            </div>
            <div class="metric">
                <span>High Severity:</span>
                <span class="metric-value" id="high-anomalies">0</span>
            </div>
        </div>

        <div class="card">
            <h3>⚠️ Alerts</h3>
            <div class="metric">
                <span>Total Alerts:</span>
                <span class="metric-value" id="total-alerts">0</span>
            </div>
            <div class="metric">
                <span>Critical:</span>
                <span class="metric-value" id="critical-alerts">0</span>
            </div>
        </div>
    </div>

    <div class="chart-container">
        <h3>📈 Cost Trends</h3>
        <canvas id="costTrendChart"></canvas>
    </div>

    <div class="chart-container">
        <h3>🍰 Service Breakdown</h3>
        <canvas id="serviceChart"></canvas>
    </div>

    <div class="dashboard-grid">
        <div class="card">
            <h3>🔔 Recent Alerts</h3>
            <button class="refresh-button" onclick="loadRecentAlerts()">Refresh</button>
            <div id="recent-alerts"></div>
        </div>

        <div class="card">
            <h3>🔍 Recent Anomalies</h3>
            <button class="refresh-button" onclick="loadAnomalies()">Refresh</button>
            <div id="recent-anomalies"></div>
        </div>
    </div>

    <script>
        // Initialize Socket.IO
        const socket = io();
        
        // Charts
        let costTrendChart, serviceChart;
        
        // Initialize charts
        function initCharts() {
            const costCtx = document.getElementById('costTrendChart').getContext('2d');
            costTrendChart = new Chart(costCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Daily Cost',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

            const serviceCtx = document.getElementById('serviceChart').getContext('2d');
            serviceChart = new Chart(serviceCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#667eea', '#764ba2', '#f093fb', '#f5576c',
                            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
                        ]
                    }]
                },
                options: {
                    responsive: true
                }
            });
        }

        // Update dashboard data
        function updateDashboard(data) {
            // Update cost summary
            if (data.cost_summary) {
                document.getElementById('total-cost').textContent = 
                    '₹' + data.cost_summary.total_cost.toFixed(2);
                document.getElementById('data-points').textContent = 
                    data.cost_summary.data_points;
            }

            // Update anomaly summary
            if (data.anomaly_summary) {
                document.getElementById('total-anomalies').textContent = 
                    data.anomaly_summary.total_anomalies;
                document.getElementById('high-anomalies').textContent = 
                    data.anomaly_summary.high_severity;
            }

            // Update alert summary
            if (data.alert_summary) {
                document.getElementById('total-alerts').textContent = 
                    data.alert_summary.total_alerts;
                document.getElementById('critical-alerts').textContent = 
                    data.alert_summary.critical_alerts;
            }

            // Update last update time
            if (data.last_update) {
                const updateTime = new Date(data.last_update);
                document.getElementById('last-update').textContent = 
                    'Last update: ' + updateTime.toLocaleTimeString();
            }
        }

        // Load cost trends
        async function loadCostTrends() {
            try {
                const response = await fetch('/api/cost-trends');
                const trends = await response.json();
                
                costTrendChart.data.labels = trends.map(t => t.date);
                costTrendChart.data.datasets[0].data = trends.map(t => t.cost);
                costTrendChart.update();
            } catch (error) {
                console.error('Error loading cost trends:', error);
            }
        }

        // Load service breakdown
        async function loadServiceBreakdown() {
            try {
                const response = await fetch('/api/service-breakdown');
                const breakdown = await response.json();
                
                serviceChart.data.labels = breakdown.map(s => s.service);
                serviceChart.data.datasets[0].data = breakdown.map(s => s.cost);
                serviceChart.update();
            } catch (error) {
                console.error('Error loading service breakdown:', error);
            }
        }

        // Load recent alerts
        async function loadRecentAlerts() {
            try {
                const response = await fetch('/api/recent-alerts');
                const alerts = await response.json();
                
                const container = document.getElementById('recent-alerts');
                container.innerHTML = '';
                
                alerts.forEach(alert => {
                    const alertDiv = document.createElement('div');
                    alertDiv.className = `alert-item alert-${alert.severity || 'medium'}`;
                    alertDiv.innerHTML = `
                        <strong>${alert.type}</strong><br>
                        Service: ${alert.service}<br>
                        Time: ${new Date(alert.timestamp).toLocaleString()}
                    `;
                    container.appendChild(alertDiv);
                });
            } catch (error) {
                console.error('Error loading recent alerts:', error);
            }
        }

        // Load anomalies
        async function loadAnomalies() {
            try {
                const response = await fetch('/api/anomalies');
                const anomalies = await response.json();
                
                const container = document.getElementById('recent-anomalies');
                container.innerHTML = '';
                
                anomalies.forEach(anomaly => {
                    const anomalyDiv = document.createElement('div');
                    anomalyDiv.className = `alert-item alert-${anomaly.severity || 'medium'}`;
                    anomalyDiv.innerHTML = `
                        <strong>Anomaly</strong><br>
                        Service: ${anomaly.service}<br>
                        Score: ${anomaly.anomaly_score}<br>
                        Time: ${new Date(anomaly.timestamp).toLocaleString()}
                    `;
                    container.appendChild(anomalyDiv);
                });
            } catch (error) {
                console.error('Error loading anomalies:', error);
            }
        }

        // Socket.IO event handlers
        socket.on('connect', () => {
            document.getElementById('status-indicator').className = 'status-indicator status-online';
            document.getElementById('status-text').textContent = 'Connected';
        });

        socket.on('disconnect', () => {
            document.getElementById('status-indicator').className = 'status-indicator status-offline';
            document.getElementById('status-text').textContent = 'Disconnected';
        });

        socket.on('data_update', (data) => {
            updateDashboard(data);
        });

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', () => {
            initCharts();
            loadCostTrends();
            loadServiceBreakdown();
            loadRecentAlerts();
            loadAnomalies();
            
            // Load initial summary
            fetch('/api/summary')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(error => console.error('Error loading summary:', error));
        });

        // Auto-refresh every 30 seconds
        setInterval(() => {
            loadCostTrends();
            loadServiceBreakdown();
            loadRecentAlerts();
            loadAnomalies();
        }, 30000);
    </script>
</body>
</html>'''
    
    with open(os.path.join(template_dir, 'dashboard.html'), 'w') as f:
        f.write(dashboard_html)

if __name__ == '__main__':
    # Create templates directory and files
    create_dashboard_templates()
    
    # Start the dashboard
    port = int(os.environ.get('DASHBOARD_PORT', 5001))
    logger.info(f"Starting dashboard on port {port}")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True) 