package data

import "time"

type DeviceReading struct {
	ID              int       `json:"id"`
	DeviceID        int64     `json:"device_id"`
	Metric          string    `json:"metric"`
	Value           float64   `json:"value"`
	Timestamp       time.Time `json:"timestamp"`
	Location        string    `json:"location,omitempty"`
	AnomalyDetected bool      `json:"anomaly_detected"`
	RollingAvg      float64   `json:"rolling_avg"`
	DeviationPct    float64   `json:"deviation_pct"`
	ProcessedAt     time.Time `json:"processed_at"`
}

type DeviceStats struct {
	DeviceID     int64     `json:"device_id"`
	MessageCount int       `json:"message_count"`
	AvgValue     float64   `json:"avg_value"`
	LastSeen     time.Time `json:"last_seen"`
	AnomalyCount int       `json:"anomaly_count"`
}
