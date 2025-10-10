package data

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

type Device struct {
	DeviceID     string    `json:"device_id"`
	MessageCount int       `json:"message_count"`
	AvgValue     float64   `json:"avg_value"`
	LastSeen     time.Time `json:"last_seen"`
	AnomalyCount int       `json:"anomaly_count"`
}

type DeviceReading struct {
	ID              int       `json:"id"`
	DeviceID        string    `json:"device_id"`
	Metric          string    `json:"metric"`
	Value           float64   `json:"value"`
	Timestamp       time.Time `json:"timestamp"`
	Location        string    `json:"location,omitempty"`
	AnomalyDetected bool      `json:"anomaly_detected"`
	RollingAvg      float64   `json:"rolling_avg"`
	DeviationPct    float64   `json:"deviation_pct"`
	ProcessedAt     time.Time `json:"processed_at"`
}

type DeviceModel struct {
	db *pgxpool.Pool
}

// GetAllDevices returns aggregate statistics for all devices.
func (d DeviceModel) GetAllDevices(ctx context.Context, activeOnly bool, limit int) ([]*Device, error) {
	query := `
        SELECT 
            device_id,
            COUNT(*) as message_count,
            AVG(value) as avg_value,
            MAX(processed_at) as last_seen,
            COUNT(*) FILTER (WHERE anomaly_detected = true) as anomaly_count
        FROM device_readings
    `

	// Add WHERE clause if filtering for active devices
	if activeOnly {
		query += `
        WHERE processed_at > NOW() - INTERVAL '5 minutes'
        `
	}

	query += `
        GROUP BY device_id
        ORDER BY last_seen DESC
        LIMIT $1
    `

	rows, err := d.db.Query(ctx, query, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var devices []*Device
	for rows.Next() {
		var device Device
		err := rows.Scan(
			&device.DeviceID,
			&device.MessageCount,
			&device.AvgValue,
			&device.LastSeen,
			&device.AnomalyCount,
		)
		if err != nil {
			return nil, err
		}
		devices = append(devices, &device)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return devices, nil
}

// GetDevice returns statistics for a single device.
func (d DeviceModel) GetDevice(ctx context.Context, deviceID string) (*Device, error) {
	query := `
        SELECT 
            device_id,
            COUNT(*) as message_count,
            AVG(value) as avg_value,
            MAX(processed_at) as last_seen,
            COUNT(*) FILTER (WHERE anomaly_detected = true) as anomaly_count
        FROM device_readings
        WHERE device_id = $1
        GROUP BY device_id
    `

	var device Device
	err := d.db.QueryRow(ctx, query, deviceID).Scan(
		&device.DeviceID,
		&device.MessageCount,
		&device.AvgValue,
		&device.LastSeen,
		&device.AnomalyCount,
	)
	if err != nil {
		return nil, err
	}

	return &device, nil
}
