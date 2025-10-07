package data

import (
	"time"
)

type SystemStats struct {
	TotalReadings  int        `json:"total_readings"`
	UniqueDevices  int        `json:"unique_devices"`
	TotalAnomalies int        `json:"total_anomalies"`
	LatestReading  *time.Time `json:"latest_reading,omitempty"`
}

type SystemHealth struct {
	Status      string `json:"status"`
	Environment string `json:"environment"`
	Version     string `json:"version"`
}
