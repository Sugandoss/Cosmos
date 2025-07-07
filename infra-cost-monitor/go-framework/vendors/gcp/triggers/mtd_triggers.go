package triggers

import (
	"infra-cost-monitor/go-framework/vendors/gcp/models"
	"log"
	"time"
)

// MTDTriggers handles month-to-date alert triggers
type MTDTriggers struct{}

// NewMTDTriggers creates a new MTD triggers instance
func NewMTDTriggers() *MTDTriggers {
	return &MTDTriggers{}
}

// CheckTriggers checks for alert conditions and returns triggered alerts
func (mt *MTDTriggers) CheckTriggers(dailyCosts []models.DailyCost, mtdCosts []models.MTDCost) []models.Alert {
	log.Println("🔔 Checking MTD triggers...")
	
	var alerts []models.Alert
	
	// Check for daily cost spikes
	if len(dailyCosts) >= 2 {
		current := dailyCosts[0].TotalCost
		previous := dailyCosts[1].TotalCost
		
		if previous > 0 {
			increase := current - previous
			percentage := (increase / previous) * 100
			
			// Trigger alert if increase > 50% or > $1000
			if percentage > 50 || increase > 1000 {
				alert := models.Alert{
					Type:    "cost_spike",
					Message: "Daily cost spike detected",
					Time:    time.Now().Format("2006-01-02 15:04:05"),
				}
				alerts = append(alerts, alert)
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
			
			// Trigger alert if increase > 30% or > $5000
			if percentage > 30 || increase > 5000 {
				alert := models.Alert{
					Type:    "monthly_spike",
					Message: "Monthly cost spike detected",
					Time:    time.Now().Format("2006-01-02 15:04:05"),
				}
				alerts = append(alerts, alert)
			}
		}
	}
	
	log.Printf("✅ MTD triggers checked - %d alerts triggered", len(alerts))
	return alerts
}

// TriggerMTDRootCause triggers root cause analysis for MTD anomalies
func (mt *MTDTriggers) TriggerMTDRootCause(anomaly models.Anomaly) {
	log.Printf("🔍 Triggering root cause analysis for anomaly: %s", anomaly.Description)
	// Implementation for root cause analysis would go here
} 