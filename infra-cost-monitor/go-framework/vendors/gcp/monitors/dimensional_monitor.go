package monitors

import (
	"cloud.google.com/go/bigquery"
	"infra-cost-monitor/go-framework/adapters/bigquery"
	"infra-cost-monitor/go-framework/vendors/gcp/models"
	"log"
)

// DimensionalMonitor monitors cost data across multiple dimensions
type DimensionalMonitor struct {
	client *bigquery.Client
}

// NewDimensionalMonitor creates a new dimensional monitor
func NewDimensionalMonitor(client *bigquery.Client) *DimensionalMonitor {
	return &DimensionalMonitor{
		client: client,
	}
}

// GetDimensionalCosts retrieves cost data grouped by multiple dimensions
func (dm *DimensionalMonitor) GetDimensionalCosts() ([]models.CostData, error) {
	log.Println("📊 Fetching dimensional cost data...")

	// Create BigQuery client
	bqClient, err := bigquery.NewClient()
	if err != nil {
		return nil, err
	}
	defer bqClient.Close()

	// Get billing data for last 90 days
	it, err := bqClient.GetBillingData(90)
	if err != nil {
		return nil, err
	}

	var dimensionalCosts []models.CostData
	for {
		var row struct {
			Date        string  `bigquery:"date"`
			Service     string  `bigquery:"service"`
			SKU         string  `bigquery:"sku"`
			ProjectID   string  `bigquery:"project_id"`
			ProjectName string  `bigquery:"project_name"`
			Region      string  `bigquery:"region"`
			Cost        float64 `bigquery:"cost"`
			UsageAmount float64 `bigquery:"usage_amount"`
			UsageUnit   string  `bigquery:"usage_unit"`
		}

		err := it.Next(&row)
		if err != nil {
			break
		}

		dimensionalCosts = append(dimensionalCosts, models.CostData{
			Date:        row.Date,
			Service:     row.Service,
			SKU:         row.SKU,
			ProjectID:   row.ProjectID,
			ProjectName: row.ProjectName,
			Region:      row.Region,
			Cost:        row.Cost,
			UsageAmount: row.UsageAmount,
			UsageUnit:   row.UsageUnit,
		})
	}

	log.Printf("✅ Retrieved %d dimensional cost records", len(dimensionalCosts))
	return dimensionalCosts, nil
}

// GetServiceBreakdown returns cost breakdown by service
func (dm *DimensionalMonitor) GetServiceBreakdown(costs []models.CostData) map[string]float64 {
	serviceCosts := make(map[string]float64)
	
	for _, cost := range costs {
		serviceCosts[cost.Service] += cost.Cost
	}
	
	return serviceCosts
}

// GetProjectBreakdown returns cost breakdown by project
func (dm *DimensionalMonitor) GetProjectBreakdown(costs []models.CostData) map[string]float64 {
	projectCosts := make(map[string]float64)
	
	for _, cost := range costs {
		projectCosts[cost.ProjectID] += cost.Cost
	}
	
	return projectCosts
}

// GetRegionBreakdown returns cost breakdown by region
func (dm *DimensionalMonitor) GetRegionBreakdown(costs []models.CostData) map[string]float64 {
	regionCosts := make(map[string]float64)
	
	for _, cost := range costs {
		regionCosts[cost.Region] += cost.Cost
	}
	
	return regionCosts
}

// GetSKUBreakdown returns cost breakdown by SKU
func (dm *DimensionalMonitor) GetSKUBreakdown(costs []models.CostData) map[string]float64 {
	skuCosts := make(map[string]float64)
	
	for _, cost := range costs {
		skuCosts[cost.SKU] += cost.Cost
	}
	
	return skuCosts
} 