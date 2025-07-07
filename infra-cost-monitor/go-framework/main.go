package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"infra-cost-monitor/go-framework/adapters/bigquery"
	"infra-cost-monitor/go-framework/vendors/gcp/models"
	"infra-cost-monitor/go-framework/vendors/gcp/monitors"
	"infra-cost-monitor/go-framework/vendors/gcp/triggers"
	"infra-cost-monitor/go-framework/vendors/gcp/utils"
)

func main() {
	log.Println("🚀 Starting GCP Cost Monitor (Go Framework)")
	log.Println("=============================================")

	// Initialize BigQuery client
	client, err := bigquery.NewClient()
	if err != nil {
		log.Fatalf("Failed to initialize BigQuery client: %v", err)
	}
	defer client.Close()

	// Initialize monitors
	dailyMonitor := monitors.NewDailyMonitor(client)
	mtdMonitor := monitors.NewMTDMonitor(client)
	dimensionalMonitor := monitors.NewDimensionalMonitor(client)

	// Initialize triggers
	mtdTriggers := triggers.NewMTDTriggers()

	// Initialize data processor
	processor := utils.NewDataProcessor()

	// Run cost monitoring
	log.Println("📊 Fetching cost data from BigQuery...")
	
	// Get daily costs
	dailyCosts, err := dailyMonitor.GetDailyCosts()
	if err != nil {
		log.Printf("Warning: Failed to get daily costs: %v", err)
	}

	// Get MTD costs
	mtdCosts, err := mtdMonitor.GetMTDCosts()
	if err != nil {
		log.Printf("Warning: Failed to get MTD costs: %v", err)
	}

	// Get dimensional costs
	dimensionalCosts, err := dimensionalMonitor.GetDimensionalCosts()
	if err != nil {
		log.Printf("Warning: Failed to get dimensional costs: %v", err)
	}

	// Process and aggregate data
	compositeData := processor.ProcessCompositeData(dailyCosts, mtdCosts, dimensionalCosts)

	// Generate output files
	log.Println("💾 Generating output files...")

	// Save composite data
	compositeJSON, err := json.MarshalIndent(compositeData, "", "  ")
	if err != nil {
		log.Printf("Error marshaling composite data: %v", err)
	} else {
		err = os.WriteFile("mock-data/output/composite_data.json", compositeJSON, 0644)
		if err != nil {
			log.Printf("Error writing composite data: %v", err)
		} else {
			log.Println("✅ Saved composite_data.json")
		}
	}

	// Save daily totals
	dailyTotals := processor.ProcessDailyTotals(dailyCosts)
	dailyJSON, err := json.MarshalIndent(dailyTotals, "", "  ")
	if err != nil {
		log.Printf("Error marshaling daily totals: %v", err)
	} else {
		err = os.WriteFile("mock-data/output/daily_total_data.json", dailyJSON, 0644)
		if err != nil {
			log.Printf("Error writing daily totals: %v", err)
		} else {
			log.Println("✅ Saved daily_total_data.json")
		}
	}

	// Save MTD data
	mtdJSON, err := json.MarshalIndent(mtdCosts, "", "  ")
	if err != nil {
		log.Printf("Error marshaling MTD data: %v", err)
	} else {
		err = os.WriteFile("mock-data/output/mtd_data.json", mtdJSON, 0644)
		if err != nil {
			log.Printf("Error writing MTD data: %v", err)
		} else {
			log.Println("✅ Saved mtd_data.json")
		}
	}

	// Generate anomalies
	anomalies := processor.DetectAnomalies(dailyCosts, mtdCosts)
	anomaliesJSON, err := json.MarshalIndent(anomalies, "", "  ")
	if err != nil {
		log.Printf("Error marshaling anomalies: %v", err)
	} else {
		err = os.WriteFile("mock-data/output/anomalies.json", anomaliesJSON, 0644)
		if err != nil {
			log.Printf("Error writing anomalies: %v", err)
		} else {
			log.Printf("✅ Saved anomalies.json (%d anomalies detected)", len(anomalies))
		}
	}

	// Generate summary
	summary := processor.GenerateSummary(compositeData, dailyTotals, mtdCosts, anomalies)
	summaryJSON, err := json.MarshalIndent(summary, "", "  ")
	if err != nil {
		log.Printf("Error marshaling summary: %v", err)
	} else {
		err = os.WriteFile("mock-data/output/summary.json", summaryJSON, 0644)
		if err != nil {
			log.Printf("Error writing summary: %v", err)
		} else {
			log.Println("✅ Saved summary.json")
		}
	}

	// Check for alerts
	log.Println("🔔 Checking for alerts...")
	alerts := mtdTriggers.CheckTriggers(dailyCosts, mtdCosts)
	if len(alerts) > 0 {
		log.Printf("⚠️  Found %d alerts", len(alerts))
		for _, alert := range alerts {
			log.Printf("   - %s: %s", alert.Type, alert.Message)
		}
	} else {
		log.Println("✅ No alerts triggered")
	}

	log.Println("🎉 Go framework completed successfully!")
	log.Printf("📁 Output files saved to: mock-data/output/")
	log.Printf("📊 Total records processed: %d", len(compositeData))
	log.Printf("🔍 Anomalies detected: %d", len(anomalies))
	log.Printf("🚨 Alerts triggered: %d", len(alerts))
} 