package data

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
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

type SystemModel struct {
	db *pgxpool.Pool
}

// Gets the total number of readings, unique devices, anomalies, and the latest reading.
func (s SystemModel) GetSystemStats(ctx context.Context) (*SystemStats, error) {
	stats := &SystemStats{}

	query := `
        SELECT 
            COUNT(*) as total_readings,
            COUNT(DISTINCT device_id) as unique_devices,
            COUNT(*) FILTER (WHERE anomaly_detected = true) as total_anomalies,
            MAX(processed_at) as latest_reading
        FROM device_readings
    `

	err := s.db.QueryRow(ctx, query).Scan(
		&stats.TotalReadings,
		&stats.UniqueDevices,
		&stats.TotalAnomalies,
		&stats.LatestReading,
	)
	if err != nil {
		return nil, err
	}

	return stats, nil
}
