package utils

import (
	"infra-cost-monitor/go-framework/vendors/gcp/models"
	"log"
	"time"
)

// DataProcessor processes cost data into various formats
type DataProcessor struct{}

// NewDataProcessor creates a new data processor
func NewDataProcessor() *DataProcessor {
	return &DataProcessor{}
}

// ProcessCompositeData processes cost data into composite format
func (dp *DataProcessor) ProcessCompositeData(dailyCosts []models.DailyCost, mtdCosts []models.MTDCost, dimensionalCosts []models.CostData) []models.CostData {
	log.Println("🔄 Processing composite data...")
	
	// For now, return the dimensional costs as composite data
	// In a real implementation, this would aggregate data by service/SKU/project/region
	return dimensionalCosts
}

// ProcessDailyTotals processes daily costs into total format
func (dp *DataProcessor) ProcessDailyTotals(dailyCosts []models.DailyCost) []models.DailyCost {
	log.Println("🔄 Processing daily totals...")
	return dailyCosts
}

// DetectAnomalies detects anomalies in cost data
func (dp *DataProcessor) DetectAnomalies(dailyCosts []models.DailyCost, mtdCosts []models.MTDCost) []models.Anomaly {
	log.Println("🔍 Detecting anomalies...")
	
	var anomalies []models.Anomaly
	
	// Check for daily cost spikes
	if len(dailyCosts) >= 2 {
		current := dailyCosts[0].TotalCost
		previous := dailyCosts[1].TotalCost
		
		if previous > 0 {
			increase := current - previous
			percentage := (increase / previous) * 100
			
			// Detect spike if increase > 50% or > $1000
			if percentage > 50 || increase > 1000 {
				anomaly := models.Anomaly{
					Date:        dailyCosts[0].Date,
					Service:     "daily_total",
					CostImpact:  increase,
					Description: "Daily cost spike detected",
					Severity:    "HIGH",
					DetectedAt:  time.Now().Format("2006-01-02 15:04:05"),
				}
				anomalies = append(anomalies, anomaly)
			}
		}
	}
	
	// Check for monthly cost spikes
	if len(mtdCosts) >= 2 {
		current := mtdCosts[0].Cost
		previous := mtdCosts[1].Cost
		
		if previous > 0 {
			increase := current - previous
			percentage := (increase / previous) * 100
			
			// Detect spike if increase > 30% or > $5000
			if percentage > 30 || increase > 5000 {
				anomaly := models.Anomaly{
					Date:        mtdCosts[0].Month,
					Service:     "monthly_total",
					CostImpact:  increase,
					Description: "Monthly cost spike detected",
					Severity:    "HIGH",
					DetectedAt:  time.Now().Format("2006-01-02 15:04:05"),
				}
				anomalies = append(anomalies, anomaly)
			}
		}
	}
	
	log.Printf("✅ Detected %d anomalies", len(anomalies))
	return anomalies
}

// GenerateSummary generates summary statistics
func (dp *DataProcessor) GenerateSummary(compositeData []models.CostData, dailyTotals []models.DailyCost, mtdCosts []models.MTDCost, anomalies []models.Anomaly) models.Summary {
	log.Println("📊 Generating summary...")
	
	summary := models.Summary{
		TotalAnomalies:   len(anomalies),
		TotalCostImpact:  0,
		TotalRecords:     len(compositeData),
		MTDRecords:       len(mtdCosts),
		DailyRecords:     len(dailyTotals),
		CompositeRecords: len(compositeData),
	}
	
	// Calculate total cost impact from anomalies
	for _, anomaly := range anomalies {
		summary.TotalCostImpact += anomaly.CostImpact
	}
	
	// Get current month cost
	if len(mtdCosts) > 0 {
		summary.CurrentMonthCost = mtdCosts[0].Cost
		summary.CurrentMonthDays = mtdCosts[0].Days
	}
	
	// Get last month cost
	if len(mtdCosts) > 1 {
		summary.LastMonthCost = mtdCosts[1].Cost
		summary.LastMonthDays = mtdCosts[1].Days
	}
	
	// Get current date cost
	if len(dailyTotals) > 0 {
		summary.CurrentDateCost = dailyTotals[0].TotalCost
	}
	
	log.Println("✅ Summary generated")
	return summary
} 