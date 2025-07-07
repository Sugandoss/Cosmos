package models

import (
	"time"
)

// CostData represents a single cost record
type CostData struct {
	Date        string  `json:"date"`
	Service     string  `json:"service"`
	SKU         string  `json:"sku"`
	ProjectID   string  `json:"project_id"`
	ProjectName string  `json:"project_name"`
	Region      string  `json:"region"`
	Cost        float64 `json:"cost"`
	UsageAmount float64 `json:"usage_amount"`
	UsageUnit   string  `json:"usage_unit"`
}

// DailyCost represents daily aggregated cost
type DailyCost struct {
	Date      string  `json:"date"`
	TotalCost float64 `json:"total_cost"`
}

// MTDCost represents month-to-date cost
type MTDCost struct {
	Month     string  `json:"month"`
	Cost      float64 `json:"cost"`
	Days      int     `json:"days"`
}

// ServiceCost represents cost by service
type ServiceCost struct {
	Service    string  `json:"service"`
	TotalCost  float64 `json:"total_cost"`
	Days       int     `json:"days"`
}

// Anomaly represents a detected cost anomaly
type Anomaly struct {
	Date        string  `json:"date"`
	Service     string  `json:"service"`
	CostImpact  float64 `json:"cost_impact"`
	Description string  `json:"description"`
	Severity    string  `json:"severity"`
	DetectedAt  string  `json:"detected_at"`
}

// Alert represents a triggered alert
type Alert struct {
	Type    string `json:"type"`
	Message string `json:"message"`
	Time    string `json:"time"`
}

// Summary represents system summary statistics
type Summary struct {
	TotalAnomalies     int     `json:"total_anomalies"`
	TotalCostImpact    float64 `json:"total_cost_impact"`
	CurrentMonthCost   float64 `json:"current_month_cost"`
	CurrentMonthDays   int     `json:"current_month_days"`
	LastMonthCost      float64 `json:"last_month_cost"`
	LastMonthDays      int     `json:"last_month_days"`
	CurrentDateCost    float64 `json:"current_date_cost"`
	TotalRecords       int     `json:"total_records"`
	MTDRecords         int     `json:"mtd_records"`
	DailyRecords       int     `json:"daily_records"`
	CompositeRecords   int     `json:"composite_records"`
} 