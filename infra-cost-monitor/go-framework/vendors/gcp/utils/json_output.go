package utils

import (
	"encoding/json"
	"infra-cost-monitor/go-framework/vendors/gcp/models"
	"log"
	"os"
)

// JSONOutput handles JSON file output operations
type JSONOutput struct{}

// NewJSONOutput creates a new JSON output handler
func NewJSONOutput() *JSONOutput {
	return &JSONOutput{}
}

// SaveCompositeData saves composite cost data to JSON file
func (jo *JSONOutput) SaveCompositeData(data []models.CostData, filename string) error {
	log.Printf("💾 Saving composite data to %s", filename)
	
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(filename, jsonData, 0644)
}

// SaveDailyTotals saves daily totals to JSON file
func (jo *JSONOutput) SaveDailyTotals(data []models.DailyCost, filename string) error {
	log.Printf("💾 Saving daily totals to %s", filename)
	
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(filename, jsonData, 0644)
}

// SaveMTDData saves MTD data to JSON file
func (jo *JSONOutput) SaveMTDData(data []models.MTDCost, filename string) error {
	log.Printf("💾 Saving MTD data to %s", filename)
	
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(filename, jsonData, 0644)
}

// SaveAnomalies saves anomalies to JSON file
func (jo *JSONOutput) SaveAnomalies(data []models.Anomaly, filename string) error {
	log.Printf("💾 Saving anomalies to %s", filename)
	
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(filename, jsonData, 0644)
}

// SaveSummary saves summary to JSON file
func (jo *JSONOutput) SaveSummary(data models.Summary, filename string) error {
	log.Printf("💾 Saving summary to %s", filename)
	
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	
	return os.WriteFile(filename, jsonData, 0644)
}

// LoadCompositeData loads composite data from JSON file
func (jo *JSONOutput) LoadCompositeData(filename string) ([]models.CostData, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}
	
	var compositeData []models.CostData
	err = json.Unmarshal(data, &compositeData)
	return compositeData, err
}

// LoadDailyTotals loads daily totals from JSON file
func (jo *JSONOutput) LoadDailyTotals(filename string) ([]models.DailyCost, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}
	
	var dailyTotals []models.DailyCost
	err = json.Unmarshal(data, &dailyTotals)
	return dailyTotals, err
}

// LoadMTDData loads MTD data from JSON file
func (jo *JSONOutput) LoadMTDData(filename string) ([]models.MTDCost, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}
	
	var mtdData []models.MTDCost
	err = json.Unmarshal(data, &mtdData)
	return mtdData, err
}

// LoadAnomalies loads anomalies from JSON file
func (jo *JSONOutput) LoadAnomalies(filename string) ([]models.Anomaly, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}
	
	var anomalies []models.Anomaly
	err = json.Unmarshal(data, &anomalies)
	return anomalies, err
} 