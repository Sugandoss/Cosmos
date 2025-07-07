#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GCP Cost Forecasting using Prophet
Provides time-series forecasting for infrastructure costs
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CostForecaster:
    def __init__(self, output_dir: str = "../output", forecasts_dir: str = "./forecasts"):
        """
        Initialize the cost forecaster
        
        Args:
            output_dir: Directory containing JSON files from Go framework
            forecasts_dir: Directory to save forecast results
        """
        self.output_dir = output_dir
        self.forecasts_dir = forecasts_dir
        
        # Create forecasts directory
        os.makedirs(forecasts_dir, exist_ok=True)
        
        logger.info("Cost Forecaster initialized")
    
    def load_cost_data(self) -> pd.DataFrame:
        """Load cost data from JSON files and prepare for forecasting"""
        try:
            # Load daily total data
            daily_file = os.path.join(self.output_dir, "daily_total_data.json")
            if not os.path.exists(daily_file):
                logger.error(f"Daily data file not found: {daily_file}")
                return pd.DataFrame()
            
            with open(daily_file, 'r') as f:
                daily_data = json.load(f)
            
            # Convert to DataFrame
            df = pd.DataFrame(daily_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Use ALL available data for forecasting (not just recent data)
            logger.info(f"Loaded {len(df)} days of cost data for forecasting")
            logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
            
            # Prophet requires columns: 'ds' (date) and 'y' (value)
            df_prophet = df.rename(columns={'date': 'ds', 'cost': 'y'})
            
            return df_prophet
            
        except Exception as e:
            logger.error(f"Error loading cost data: {e}")
            return pd.DataFrame()
    
    def create_service_forecasts(self) -> Dict[str, pd.DataFrame]:
        """Create forecasts for individual services"""
        try:
            # Load composite data for service-level forecasting
            composite_file = os.path.join(self.output_dir, "composite_data.json")
            if not os.path.exists(composite_file):
                logger.warning("Composite data file not found, skipping service forecasts")
                return {}
            
            with open(composite_file, 'r') as f:
                composite_data = json.load(f)
            
            # Group by service
            service_forecasts = {}
            
            for service in set(item['service_desc'] for item in composite_data):
                service_data = [item for item in composite_data if item['service_desc'] == service]
                
                # Aggregate daily costs by service using ALL available data
                df_service = pd.DataFrame(service_data)
                df_service['date'] = pd.to_datetime(df_service['date'])
                daily_service_costs = df_service.groupby('date')['cost'].sum().reset_index()
                daily_service_costs = daily_service_costs.rename(columns={'date': 'ds', 'cost': 'y'})
                
                if len(daily_service_costs) >= 7:  # Need at least 7 days for forecasting
                    service_forecasts[service] = daily_service_costs
                    logger.info(f"Prepared forecast data for {service}: {len(daily_service_costs)} days")
                    logger.info(f"  Date range: {daily_service_costs['ds'].min()} to {daily_service_costs['ds'].max()}")
            
            return service_forecasts
            
        except Exception as e:
            logger.error(f"Error creating service forecasts: {e}")
            return {}
    
    def run_forecast(self, df: pd.DataFrame, periods: int = 30, service_name: str = "Total Cost") -> Dict[str, Any]:
        """
        Run Prophet forecast on cost data
        
        Args:
            df: DataFrame with 'ds' and 'y' columns
            periods: Number of days to forecast
            service_name: Name of the service being forecasted
        
        Returns:
            Dictionary containing forecast results
        """
        try:
            logger.info(f"Running forecast for {service_name} ({periods} days)")
            
            # Initialize Prophet model with settings optimized for 1 year of data
            model = Prophet(
                yearly_seasonality=True,      # Capture yearly patterns
                weekly_seasonality=True,      # Capture weekly patterns  
                daily_seasonality=False,      # Too granular for cost data
                seasonality_mode='multiplicative',  # Better for cost data
                changepoint_prior_scale=0.05,  # Allow for trend changes
                seasonality_prior_scale=10.0   # Allow seasonality to vary
            )
            
            # Fit the model
            model.fit(df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=periods)
            
            # Make forecast
            forecast = model.predict(future)
            
            # Extract forecast components
            forecast_result = {
                'service': service_name,
                'forecast_dates': forecast['ds'].tail(periods).dt.strftime('%Y-%m-%d').tolist(),
                'forecast_values': forecast['yhat'].tail(periods).tolist(),
                'forecast_lower': forecast['yhat_lower'].tail(periods).tolist(),
                'forecast_upper': forecast['yhat_upper'].tail(periods).tolist(),
                'trend': forecast['trend'].tail(periods).tolist(),
                'seasonal': forecast['yearly'].tail(periods).tolist(),
                'last_actual_date': df['ds'].max().strftime('%Y-%m-%d'),
                'last_actual_value': float(df['y'].iloc[-1]),
                'forecast_periods': periods
            }
            
            # Save forecast to file
            forecast_file = os.path.join(self.forecasts_dir, f"{service_name.lower().replace(' ', '_')}_forecast.json")
            with open(forecast_file, 'w') as f:
                json.dump(forecast_result, f, indent=2)
            
            logger.info(f"Forecast completed for {service_name}")
            return forecast_result
            
        except Exception as e:
            logger.error(f"Error running forecast for {service_name}: {e}")
            return {}
    
    def run_all_forecasts(self, forecast_days: int = 30) -> Dict[str, Any]:
        """Run forecasts for total costs and individual services"""
        logger.info("Starting cost forecasting pipeline...")
        
        results = {
            'total_cost_forecast': {},
            'service_forecasts': {},
            'summary': {}
        }
        
        # Total cost forecast
        df_total = self.load_cost_data()
        if not df_total.empty:
            results['total_cost_forecast'] = self.run_forecast(df_total, forecast_days, "Total Cost")
        
        # Service-level forecasts
        service_data = self.create_service_forecasts()
        for service, df_service in service_data.items():
            forecast_result = self.run_forecast(df_service, forecast_days, service)
            if forecast_result:
                results['service_forecasts'][service] = forecast_result
        
        # Create summary
        results['summary'] = {
            'total_services_forecasted': len(results['service_forecasts']),
            'forecast_days': forecast_days,
            'forecast_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_forecast_value': sum(results['total_cost_forecast'].get('forecast_values', [])),
            'services': list(results['service_forecasts'].keys())
        }
        
        # Save summary
        summary_file = os.path.join(self.forecasts_dir, "forecast_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(results['summary'], f, indent=2)
        
        logger.info("Cost forecasting pipeline completed!")
        return results
    
    def get_forecast_insights(self, forecast_results: Dict[str, Any]) -> List[str]:
        """Generate insights from forecast results"""
        insights = []
        
        total_forecast = forecast_results.get('total_cost_forecast', {})
        if total_forecast:
            # Calculate trend
            forecast_values = total_forecast.get('forecast_values', [])
            if len(forecast_values) >= 2:
                trend = (forecast_values[-1] - forecast_values[0]) / forecast_values[0] * 100
                
                if trend > 10:
                    insights.append(f"📈 Cost trend is increasing by {trend:.1f}% over the next {total_forecast.get('forecast_periods', 0)} days")
                elif trend < -10:
                    insights.append(f"📉 Cost trend is decreasing by {abs(trend):.1f}% over the next {total_forecast.get('forecast_periods', 0)} days")
                else:
                    insights.append(f"➡️ Cost trend is relatively stable with {trend:.1f}% change")
            
            # Peak prediction
            max_forecast = max(forecast_values) if forecast_values else 0
            max_date_idx = forecast_values.index(max_forecast) if forecast_values else 0
            max_date = total_forecast.get('forecast_dates', [])[max_date_idx] if total_forecast.get('forecast_dates') else ""
            
            insights.append(f"🎯 Predicted peak cost: ₹{max_forecast:.2f} on {max_date}")
        
        # Service insights
        service_forecasts = forecast_results.get('service_forecasts', {})
        if service_forecasts:
            # Find fastest growing service
            max_growth_service = None
            max_growth = 0
            
            for service, forecast in service_forecasts.items():
                values = forecast.get('forecast_values', [])
                if len(values) >= 2:
                    growth = (values[-1] - values[0]) / values[0] * 100
                    if growth > max_growth:
                        max_growth = growth
                        max_growth_service = service
            
            if max_growth_service:
                insights.append(f"🚀 {max_growth_service} shows the highest growth trend: {max_growth:.1f}%")
        
        return insights

def main():
    """Main function to run cost forecasting"""
    forecaster = CostForecaster()
    results = forecaster.run_all_forecasts(forecast_days=30)
    
    if results:
        print("✅ Cost forecasting completed!")
        print(f"   - Total cost forecast: {'✅' if results['total_cost_forecast'] else '❌'}")
        print(f"   - Service forecasts: {results['summary']['total_services_forecasted']}")
        print(f"   - Forecast period: {results['summary']['forecast_days']} days")
        print(f"   - Results saved to: ./forecasts/")
        
        # Show insights
        insights = forecaster.get_forecast_insights(results)
        if insights:
            print("\n📊 Forecast Insights:")
            for insight in insights:
                print(f"   {insight}")

if __name__ == "__main__":
    main() 