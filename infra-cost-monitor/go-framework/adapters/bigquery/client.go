package bigquery

import (
	"context"
	"fmt"
	"log"
	"os"

	"cloud.google.com/go/bigquery"
	"google.golang.org/api/option"
)

// Client represents a BigQuery client
type Client struct {
	client *bigquery.Client
	ctx    context.Context
}

// NewClient creates a new BigQuery client
func NewClient() (*Client, error) {
	ctx := context.Background()

	// Get project ID from environment or use default
	projectID := os.Getenv("GOOGLE_CLOUD_PROJECT")
	if projectID == "" {
		projectID = "your-gcp-project-id" // Replace with your actual project ID
	}

	// Create client with default credentials
	client, err := bigquery.NewClient(ctx, projectID)
	if err != nil {
		return nil, fmt.Errorf("failed to create BigQuery client: %v", err)
	}

	return &Client{
		client: client,
		ctx:    ctx,
	}, nil
}

// Close closes the BigQuery client
func (c *Client) Close() error {
	return c.client.Close()
}

// Query executes a BigQuery SQL query
func (c *Client) Query(query string) (*bigquery.RowIterator, error) {
	q := c.client.Query(query)
	return q.Read(c.ctx)
}

// GetBillingData retrieves cost data from BigQuery billing export
func (c *Client) GetBillingData(days int) (*bigquery.RowIterator, error) {
	query := fmt.Sprintf(`
		SELECT 
			DATE(usage_start_time) as date,
			service.description as service,
			sku.description as sku,
			project.id as project_id,
			project.name as project_name,
			location.location as region,
			SUM(cost) as cost,
			SUM(usage.amount) as usage_amount,
			usage.unit as usage_unit
		FROM `+"`%s.%s.%s`"+`
		WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL %d DAY)
		AND service.description NOT LIKE '%%Marketplace%%'
		GROUP BY date, service, sku, project_id, project_name, region, usage_unit
		ORDER BY date DESC, cost DESC
	`, 
		os.Getenv("BIGQUERY_DATASET"), 
		os.Getenv("BIGQUERY_TABLE"), 
		os.Getenv("BIGQUERY_BILLING_EXPORT_TABLE"),
		days)

	return c.Query(query)
}

// GetDailyCosts retrieves daily aggregated costs
func (c *Client) GetDailyCosts(days int) (*bigquery.RowIterator, error) {
	query := fmt.Sprintf(`
		SELECT 
			DATE(usage_start_time) as date,
			SUM(cost) as total_cost
		FROM `+"`%s.%s.%s`"+`
		WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL %d DAY)
		AND service.description NOT LIKE '%%Marketplace%%'
		GROUP BY date
		ORDER BY date DESC
	`,
		os.Getenv("BIGQUERY_DATASET"), 
		os.Getenv("BIGQUERY_TABLE"), 
		os.Getenv("BIGQUERY_BILLING_EXPORT_TABLE"),
		days)

	return c.Query(query)
}

// GetServiceCosts retrieves costs by service
func (c *Client) GetServiceCosts(days int) (*bigquery.RowIterator, error) {
	query := fmt.Sprintf(`
		SELECT 
			service.description as service,
			SUM(cost) as total_cost,
			COUNT(DISTINCT DATE(usage_start_time)) as days
		FROM `+"`%s.%s.%s`"+`
		WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL %d DAY)
		AND service.description NOT LIKE '%%Marketplace%%'
		GROUP BY service
		ORDER BY total_cost DESC
	`,
		os.Getenv("BIGQUERY_DATASET"), 
		os.Getenv("BIGQUERY_TABLE"), 
		os.Getenv("BIGQUERY_BILLING_EXPORT_TABLE"),
		days)

	return c.Query(query)
} 