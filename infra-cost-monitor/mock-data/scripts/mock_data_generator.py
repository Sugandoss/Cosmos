#!/usr/bin/env python3
"""
Mock Data Generator for GCP Cost Monitoring System
Creates 1 year of realistic cost data with anomalies for testing Slack alerts
"""

import json
import random
import datetime
from typing import List, Dict, Any
import os

class MockDataGenerator:
    def __init__(self):
        self.services = [
            "BigQuery", "Cloud Functions", "Cloud Run", "Cloud SQL", 
            "Cloud Storage", "Compute Engine", "Kubernetes Engine", "Pub/Sub"
        ]
        
        self.skus = [
            "N2 Custom Instance Ram running in Mumbai",
            "Cloud SQL for MySQL",
            "Standard Storage",
            "BigQuery Analysis",
            "Cloud Functions (1st Gen)",
            "Cloud Run",
            "Pub/Sub Lite",
            "Kubernetes Engine"
        ]
        
        self.projects = [
            "gw-backend-production", "gw-analytics", "gw-data-processing",
            "gw-backend-staging", "gw-frontend-production"
        ]
        
        self.regions = [
            "asia-southeast1", "us-central1", "europe-west1", 
            "asia-south1", "us-east1"
        ]
        
        # Realistic GCP cost ranges (in USD) based on typical enterprise usage
        self.base_costs = {
            "BigQuery": {"min": 50.0, "max": 500.0},           # Query processing + storage
            "Cloud Functions": {"min": 20.0, "max": 200.0},      # Function invocations + compute
            "Cloud Run": {"min": 30.0, "max": 300.0},            # Container instances + requests
            "Cloud SQL": {"min": 100.0, "max": 800.0},           # Database instances + storage
            "Cloud Storage": {"min": 10.0, "max": 150.0},        # Storage + operations
            "Compute Engine": {"min": 200.0, "max": 2000.0},     # VM instances + persistent disks
            "Kubernetes Engine": {"min": 80.0, "max": 600.0},    # Cluster management + nodes
            "Pub/Sub": {"min": 15.0, "max": 180.0}              # Message throughput + storage
        }
        
        # Define realistic anomaly patterns with moderate multipliers
        self.anomaly_patterns = [
            {"date": "2024-12-15", "service": "Compute Engine", "multiplier": 3.5, "description": "Spike in compute costs due to Black Friday traffic"},
            {"date": "2025-01-20", "service": "BigQuery", "multiplier": 4.2, "description": "Massive BigQuery usage spike during data migration"},
            {"date": "2025-02-10", "service": "Cloud SQL", "multiplier": 2.8, "description": "Database performance issues causing increased costs"},
            {"date": "2025-03-05", "service": "Kubernetes Engine", "multiplier": 3.0, "description": "K8s cluster scaling anomaly during deployment"},
            {"date": "2025-04-12", "service": "Cloud Functions", "multiplier": 4.5, "description": "Function execution spike during API load testing"},
            {"date": "2025-05-18", "service": "Cloud Storage", "multiplier": 2.5, "description": "Storage cost anomaly due to backup operations"},
            {"date": "2025-06-25", "service": "Pub/Sub", "multiplier": 3.2, "description": "Message processing spike during event processing"},
            {"date": "2025-07-08", "service": "Cloud Run", "multiplier": 2.8, "description": "Container scaling issue during traffic surge"}
        ]

    def generate_date_range(self, start_date: str, days: int) -> List[str]:
        """Generate list of dates from start_date for specified number of days"""
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        dates = []
        for i in range(days):
            date = start + datetime.timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
        return dates

    def is_anomaly_date(self, date: str, service: str) -> float:
        """Check if date has anomaly for specific service"""
        for pattern in self.anomaly_patterns:
            if pattern["date"] == date and pattern["service"] == service:
                return pattern["multiplier"]
        return 1.0

    def generate_realistic_cost(self, service: str, base_multiplier: float = 1.0) -> float:
        """Generate realistic cost with some randomness"""
        base_range = self.base_costs[service]
        base_cost = random.uniform(base_range["min"], base_range["max"])
        
        # Add some daily variation (±25%)
        daily_variation = random.uniform(0.75, 1.25)
        
        # Add weekend effect (lower costs on weekends)
        current_date = datetime.datetime.now()
        if current_date.weekday() >= 5:  # Weekend
            daily_variation *= 0.85
        
        return round(base_cost * daily_variation * base_multiplier, 2)

    def generate_composite_data(self, start_date: str = "2024-07-01", days: int = 365) -> List[Dict[str, Any]]:
        """Generate composite cost data for specified period"""
        dates = self.generate_date_range(start_date, days)
        composite_data = []
        
        print(f"Generating {days} days of composite data from {start_date}...")
        
        # First, ensure anomaly dates have records for their services
        anomaly_dates_processed = set()
        
        for pattern in self.anomaly_patterns:
            anomaly_date = pattern["date"]
            anomaly_service = pattern["service"]
            anomaly_multiplier = pattern["multiplier"]
            
            # Generate 3-5 records for this anomaly
            for _ in range(random.randint(3, 5)):
                sku = random.choice(self.skus)
                project = random.choice(self.projects)
                region = random.choice(self.regions)
                
                cost = self.generate_realistic_cost(anomaly_service, anomaly_multiplier)
                
                record = {
                    "service_desc": anomaly_service,
                    "sku_desc": sku,
                    "project_id": project,
                    "region": region,
                    "date": anomaly_date,
                    "cost": cost
                }
                composite_data.append(record)
            
            anomaly_dates_processed.add(anomaly_date)
        
        # Then generate regular data for all dates
        for date in dates:
            # Skip dates that already have anomaly records
            if date in anomaly_dates_processed:
                continue
                
            # Generate 3-8 records per day
            daily_records = random.randint(3, 8)
            
            for _ in range(daily_records):
                service = random.choice(self.services)
                sku = random.choice(self.skus)
                project = random.choice(self.projects)
                region = random.choice(self.regions)
                
                # Check for anomalies (should be 1.0 for non-anomaly dates)
                anomaly_multiplier = self.is_anomaly_date(date, service)
                cost = self.generate_realistic_cost(service, anomaly_multiplier)
                
                record = {
                    "service_desc": service,
                    "sku_desc": sku,
                    "project_id": project,
                    "region": region,
                    "date": date,
                    "cost": cost
                }
                
                composite_data.append(record)
        
        # Sort by date
        composite_data.sort(key=lambda x: x["date"])
        
        print(f"Generated {len(composite_data)} composite records")
        return composite_data

    def generate_daily_totals(self, composite_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate daily total cost data from composite data"""
        daily_costs = {}
        
        for record in composite_data:
            date = record["date"]
            cost = record["cost"]
            
            if date not in daily_costs:
                daily_costs[date] = 0.0
            daily_costs[date] += cost
        
        daily_data = [
            {"date": date, "cost": round(cost, 2)}
            for date, cost in sorted(daily_costs.items())
        ]
        
        print(f"Generated {len(daily_data)} daily total records")
        return daily_data

    def generate_mtd_data(self, daily_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate month-to-date cost data"""
        monthly_costs = {}
        
        for record in daily_data:
            date = datetime.datetime.strptime(record["date"], "%Y-%m-%d")
            month_key = date.strftime("%Y%m")
            cost = record["cost"]
            
            if month_key not in monthly_costs:
                monthly_costs[month_key] = {"cost": 0.0, "days": 0}
            
            monthly_costs[month_key]["cost"] += cost
            monthly_costs[month_key]["days"] += 1
        
        mtd_data = [
            {
                "month": month,
                "cost": round(data["cost"], 2),
                "days": data["days"]
            }
            for month, data in sorted(monthly_costs.items(), reverse=True)
        ]
        
        print(f"Generated {len(mtd_data)} MTD records")
        return mtd_data

    def generate_anomalies(self, composite_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate anomaly records based on anomaly patterns"""
        anomalies = []
        
        for pattern in self.anomaly_patterns:
            # Find records for this anomaly
            anomaly_records = [
                record for record in composite_data
                if record["date"] == pattern["date"] and record["service_desc"] == pattern["service"]
            ]
            
            if anomaly_records:
                total_cost = sum(record["cost"] for record in anomaly_records)
                
                anomaly = {
                    "date": pattern["date"],
                    "service": pattern["service"],
                    "cost_impact": round(total_cost, 2),
                    "description": pattern["description"],
                    "severity": "HIGH" if pattern["multiplier"] > 5.0 else "MEDIUM",
                    "detected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                anomalies.append(anomaly)
        
        print(f"Generated {len(anomalies)} anomaly records")
        return anomalies

    def generate_summary(self, composite_data: List[Dict[str, Any]], 
                        daily_data: List[Dict[str, Any]], 
                        mtd_data: List[Dict[str, Any]], 
                        anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_anomalies = len(anomalies)
        total_cost_impact = sum(anomaly["cost_impact"] for anomaly in anomalies)
        
        current_month_cost = mtd_data[0]["cost"] if mtd_data else 0
        current_month_days = mtd_data[0]["days"] if mtd_data else 0
        last_month_cost = mtd_data[1]["cost"] if len(mtd_data) > 1 else 0
        last_month_days = mtd_data[1]["days"] if len(mtd_data) > 1 else 0
        
        current_date_cost = daily_data[-1]["cost"] if daily_data else 0
        
        summary = {
            "total_anomalies": total_anomalies,
            "total_cost_impact": round(total_cost_impact, 2),
            "current_month_cost": round(current_month_cost, 2),
            "current_month_days": current_month_days,
            "last_month_cost": round(last_month_cost, 2),
            "last_month_days": last_month_days,
            "current_date_cost": round(current_date_cost, 2),
            "total_records": len(composite_data),
            "mtd_records": len(mtd_data),
            "daily_records": len(daily_data),
            "composite_records": len(composite_data)
        }
        
        print(f"Generated summary with {total_anomalies} anomalies")
        return summary

    def save_data(self, output_dir: str = "output"):
        """Generate and save all mock data files"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate data
        composite_data = self.generate_composite_data()
        daily_data = self.generate_daily_totals(composite_data)
        mtd_data = self.generate_mtd_data(daily_data)
        anomalies = self.generate_anomalies(composite_data)
        summary = self.generate_summary(composite_data, daily_data, mtd_data, anomalies)
        
        # Save files
        files_to_save = {
            "composite_data.json": composite_data,
            "daily_total_data.json": daily_data,
            "mtd_data.json": mtd_data,
            "anomalies.json": anomalies,
            "summary.json": summary
        }
        
        # Debug print for anomalies
        print("DEBUG: anomalies to be saved:", anomalies)
        print("DEBUG: anomalies type:", type(anomalies))
        print("DEBUG: anomalies length:", len(anomalies) if anomalies else "None")
        
        for filename, data in files_to_save.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Saved {filename}")
        
        # Print anomaly summary for testing
        print("\n" + "="*60)
        print("ANOMALY SUMMARY FOR SLACK ALERT TESTING")
        print("="*60)
        for anomaly in anomalies:
            print(f"📊 {anomaly['date']}: {anomaly['service']} - ${anomaly['cost_impact']:.2f}")
            print(f"   Severity: {anomaly['severity']} | {anomaly['description']}")
        print("="*60)
        print(f"\nTotal anomalies: {len(anomalies)}")
        print(f"Total cost impact: ${summary['total_cost_impact']:.2f}")
        print("\n🎯 Now test your Slack bot with queries like:")
        print("   - 'Show me cost anomalies'")
        print("   - 'What happened on 2025-01-20?'")
        print("   - 'Alert me about BigQuery costs'")

def main():
    """Main function to generate mock data"""
    print("🚀 GCP Cost Monitoring - Mock Data Generator")
    print("="*50)
    
    generator = MockDataGenerator()
    generator.save_data()
    
    print("\n✅ Mock data generation complete!")
    print("📁 Check the 'output/' directory for generated files")
    print("🔔 Your Slack bot should now detect these anomalies!")

if __name__ == "__main__":
    main() 