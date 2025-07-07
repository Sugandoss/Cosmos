package monitors

import (
	"fmt"
	"sort"
	"time"
	"infra-cost-monitor/vendors/gcp/models"
)

// DailyMonitor handles daily cost monitoring
type DailyMonitor struct {
	processor *models.CostDataProcessor
}

// NewDailyMonitor creates a new daily monitor
func NewDailyMonitor(processor *models.CostDataProcessor) *DailyMonitor {
	return &DailyMonitor{
		processor: processor,
	}
}

// RunDailyTests runs all daily tests and returns anomalies
func (d *DailyMonitor) RunDailyTests(anomalies *models.AnomalyCollection) {
	fmt.Println("Running Daily Cost Tests...")
	
	// Test 1: Daily total cost test (99th percentile)
	d.testDailyTotalCost(anomalies)
	
	// Test 2: Daily composite cost test (99th percentile)
	d.testDailyCompositeCost(anomalies)
}

// testDailyTotalCost tests if current date cost is above 99th percentile
func (d *DailyMonitor) testDailyTotalCost(anomalies *models.AnomalyCollection) {
	if len(d.processor.DailyTotalData) < 90 {
		fmt.Println("Warning: Less than 90 days of data available for daily total cost test")
		return
	}
	
	// Calculate 99th percentile
	costs := make([]float64, len(d.processor.DailyTotalData))
	for i, record := range d.processor.DailyTotalData {
		costs[i] = record.Cost
	}
	
	sort.Float64s(costs)
	percentileIndex := int(float64(len(costs)) * 0.99)
	if percentileIndex >= len(costs) {
		percentileIndex = len(costs) - 1
	}
	
	percentile99 := costs[percentileIndex]
	currentCost := d.processor.GetCurrentDateCost()
	
	if currentCost > percentile99 {
		// Calculate difference margin
		differenceMargin := currentCost - percentile99
		percentageDiff := (differenceMargin / percentile99) * 100
		
		anomaly := models.Anomaly{
			TestName:       "Daily Total Cost Monitor - 99th Percentile",
			Description:    fmt.Sprintf("Current date cost (₹%.2f) is above 99th percentile (₹%.2f)", currentCost, percentile99),
			CostImpact:     currentCost,
			PercentageDiff: percentageDiff,
			CurrentValue:   currentCost,
			PreviousValue:  percentile99,
			Threshold:      percentile99,
			Timestamp:      time.Now().Format(time.RFC3339),
			Severity:       getSeverity(percentageDiff),
		}
		
		anomalies.AddAnomaly(anomaly)
	}
}

// testDailyCompositeCost tests if current date composite costs are above 99th percentile
func (d *DailyMonitor) testDailyCompositeCost(anomalies *models.AnomalyCollection) {
	if len(d.processor.CompositeData) == 0 {
		fmt.Println("Warning: No composite data available for daily composite cost test")
		return
	}
	
	// Group composite data by composite key
	compositeCosts := make(map[string][]float64)
	
	for _, record := range d.processor.CompositeData {
		key := record.CompositeKey()
		compositeCosts[key] = append(compositeCosts[key], record.Cost)
	}
	
	// Get current date composite costs
	currentDateCosts := d.processor.GetCurrentDateCompositeCosts()
	
	// Test each composite key
	for compositeKey, currentCost := range currentDateCosts {
		historicalCosts, exists := compositeCosts[compositeKey]
		if !exists || len(historicalCosts) < 90 {
			continue // Skip if not enough historical data
		}
		
		// Calculate 99th percentile for this composite key
		sort.Float64s(historicalCosts)
		percentileIndex := int(float64(len(historicalCosts)) * 0.99)
		if percentileIndex >= len(historicalCosts) {
			percentileIndex = len(historicalCosts) - 1
		}
		
		percentile99 := historicalCosts[percentileIndex]
		
		if currentCost > percentile99 {
			// Calculate difference margin
			differenceMargin := currentCost - percentile99
			percentageDiff := (differenceMargin / percentile99) * 100
			
			anomaly := models.Anomaly{
				TestName:       "Daily Composite Cost Monitor - 99th Percentile",
				Description:    fmt.Sprintf("Composite cost for %s (₹%.2f) is above 99th percentile (₹%.2f)", compositeKey, currentCost, percentile99),
				CostImpact:     currentCost,
				PercentageDiff: percentageDiff,
				CurrentValue:   currentCost,
				PreviousValue:  percentile99,
				Threshold:      percentile99,
				CompositeKey:   compositeKey,
				Timestamp:      time.Now().Format(time.RFC3339),
				Severity:       getSeverity(percentageDiff),
			}
			
			anomalies.AddAnomaly(anomaly)
		}
	}
} 