package main

import (
	"fmt"
	"log"

	"infra-cost-monitor/go-framework/adapters/bigquery"
	"infra-cost-monitor/go-framework/vendors/gcp/monitors"
)

// Demo function to test BigQuery connection and basic functionality
func demo() {
	log.Println("🧪 Running Go Framework Demo")
	log.Println("=============================")

	// Test BigQuery connection
	log.Println("1. Testing BigQuery connection...")
	client, err := bigquery.NewClient()
	if err != nil {
		log.Printf("❌ BigQuery connection failed: %v", err)
		return
	}
	defer client.Close()
	log.Println("✅ BigQuery connection successful")

	// Test daily monitor
	log.Println("2. Testing daily monitor...")
	dailyMonitor := monitors.NewDailyMonitor(client)
	dailyCosts, err := dailyMonitor.GetDailyCosts()
	if err != nil {
		log.Printf("❌ Daily monitor failed: %v", err)
	} else {
		log.Printf("✅ Daily monitor successful - %d records", len(dailyCosts))
	}

	// Test MTD monitor
	log.Println("3. Testing MTD monitor...")
	mtdMonitor := monitors.NewMTDMonitor(client)
	mtdCosts, err := mtdMonitor.GetMTDCosts()
	if err != nil {
		log.Printf("❌ MTD monitor failed: %v", err)
	} else {
		log.Printf("✅ MTD monitor successful - %d records", len(mtdCosts))
	}

	// Test dimensional monitor
	log.Println("4. Testing dimensional monitor...")
	dimensionalMonitor := monitors.NewDimensionalMonitor(client)
	dimensionalCosts, err := dimensionalMonitor.GetDimensionalCosts()
	if err != nil {
		log.Printf("❌ Dimensional monitor failed: %v", err)
	} else {
		log.Printf("✅ Dimensional monitor successful - %d records", len(dimensionalCosts))
	}

	log.Println("🎉 Demo completed successfully!")
}

func main() {
	demo()
} 