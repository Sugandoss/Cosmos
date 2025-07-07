package monitors

import (
	"cloud.google.com/go/bigquery"
	"infra-cost-monitor/go-framework/adapters/bigquery"
	"infra-cost-monitor/go-framework/vendors/gcp/models"
	"log"
	"time"
)

// MTDMonitor monitors month-to-date cost data
type MTDMonitor struct {
	client *bigquery.Client
}

// NewMTDMonitor creates a new MTD monitor
func NewMTDMonitor(client *bigquery.Client) *MTDMonitor {
	return &MTDMonitor{
		client: client,
	}
}

// GetMTDCosts retrieves month-to-date cost data from BigQuery
func (dm *MTDMonitor) GetMTDCosts() ([]models.MTDCost, error) {
	log.Println("📊 Fetching MTD cost data...")

	// Create BigQuery client
	bqClient, err := bigquery.NewClient()
	if err != nil {
		return nil, err
	}
	defer bqClient.Close()

	// Get billing data for last 7 months
	it, err := bqClient.GetBillingData(210) // 7 months * 30 days
	if err != nil {
		return nil, err
	}

	// Group by month
	monthlyCosts := make(map[string]float64)
	monthlyDays := make(map[string]int)

	for {
		var row struct {
			Date string  `bigquery:"date"`
			Cost float64 `bigquery:"cost"`
		}

		err := it.Next(&row)
		if err != nil {
			break
		}

		// Extract month from date (YYYY-MM format)
		if len(row.Date) >= 7 {
			month := row.Date[:7] // YYYY-MM
			monthlyCosts[month] += row.Cost
			
			// Count unique days in this month
			if monthlyDays[month] == 0 {
				monthlyDays[month] = 1
			}
		}
	}

	// Convert to slice
	var mtdCosts []models.MTDCost
	for month, cost := range monthlyCosts {
		days := monthlyDays[month]
		mtdCosts = append(mtdCosts, models.MTDCost{
			Month: month,
			Cost:  cost,
			Days:  days,
		})
	}

	log.Printf("✅ Retrieved %d MTD cost records", len(mtdCosts))
	return mtdCosts, nil
}

// GetCurrentMonthCost returns the cost for the current month
func (dm *MTDMonitor) GetCurrentMonthCost(mtdCosts []models.MTDCost) (float64, int) {
	if len(mtdCosts) == 0 {
		return 0, 0
	}
	
	current := mtdCosts[0] // First record is most recent
	return current.Cost, current.Days
}

// GetLastMonthCost returns the cost for the last month
func (dm *MTDMonitor) GetLastMonthCost(mtdCosts []models.MTDCost) (float64, int) {
	if len(mtdCosts) < 2 {
		return 0, 0
	}
	
	last := mtdCosts[1] // Second record is last month
	return last.Cost, last.Days
}

// CalculateMonthlySpike calculates if there's a cost spike between months
func (dm *MTDMonitor) CalculateMonthlySpike(current, previous float64, threshold float64) (bool, float64, float64) {
	if previous == 0 {
		return false, 0, 0
	}

	increase := current - previous
	percentage := (increase / previous) * 100

	return increase > threshold || percentage > 10.0, increase, percentage
} 