package data

import (
	"context"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

type ReadingModel struct {
	db *pgxpool.Pool
}

// GetReadings returns readings across all devices with optional filters.
func (r ReadingModel) GetReadings(ctx context.Context, metric string, anomalyOnly bool, start, end *time.Time, limit, offset int) ([]*DeviceReading, error) {
	query := `
        SELECT 
            id,
            device_id,
            metric,
            value,
            timestamp,
            location,
            anomaly_detected,
            rolling_avg,
            deviation_pct,
            processed_at
        FROM device_readings
        WHERE 1=1
    ` // Including `WHERE 1=1` makes it easier to optionally add more conditions

	args := []any{}
	argPos := 1

	// Add optional filters
	if metric != "" {
		query += fmt.Sprintf(" AND metric = $%d", argPos)
		args = append(args, metric)
		argPos++
	}

	if anomalyOnly {
		query += " AND anomaly_detected = true"
	}

	if start != nil {
		query += fmt.Sprintf(" AND timestamp >= $%d", argPos)
		args = append(args, *start)
		argPos++
	}

	if end != nil {
		query += fmt.Sprintf(" AND timestamp <= $%d", argPos)
		args = append(args, *end)
		argPos++
	}

	query += fmt.Sprintf(" ORDER BY timestamp DESC LIMIT $%d OFFSET $%d", argPos, argPos+1)
	args = append(args, limit, offset)

	rows, err := r.db.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var readings []*DeviceReading
	for rows.Next() {
		var reading DeviceReading

		err := rows.Scan(
			&reading.ID,
			&reading.DeviceID,
			&reading.Metric,
			&reading.Value,
			&reading.Timestamp,
			&reading.Location,
			&reading.AnomalyDetected,
			&reading.RollingAvg,
			&reading.DeviationPct,
			&reading.ProcessedAt,
		)
		if err != nil {
			return nil, err
		}

		readings = append(readings, &reading)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return readings, nil
}

// GetLatestReadings returns the most recent reading for each device (system snapshot).
func (r ReadingModel) GetLatestReadings(ctx context.Context, metric string, activeOnly bool) ([]*DeviceReading, error) {
	query := `
        SELECT DISTINCT ON (device_id)
            id,
            device_id,
            metric,
            value,
            timestamp,
            location,
            anomaly_detected,
            rolling_avg,
            deviation_pct,
            processed_at
        FROM device_readings
        WHERE 1=1
    ` // Including `WHERE 1=1` makes it easier to optionally add more conditions

	args := []any{}
	argPos := 1

	// Add optional filters
	if metric != "" {
		query += fmt.Sprintf(" AND metric = $%d", argPos)
		args = append(args, metric)
		argPos++
	}

	if activeOnly {
		query += " AND processed_at > NOW() - INTERVAL '5 minutes'"
	}

	// DISTINCT ON requires matching ORDER BY
	query += " ORDER BY device_id, timestamp DESC"

	rows, err := r.db.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var readings []*DeviceReading
	for rows.Next() {
		var reading DeviceReading

		err := rows.Scan(
			&reading.ID,
			&reading.DeviceID,
			&reading.Metric,
			&reading.Value,
			&reading.Timestamp,
			&reading.Location,
			&reading.AnomalyDetected,
			&reading.RollingAvg,
			&reading.DeviationPct,
			&reading.ProcessedAt,
		)
		if err != nil {
			return nil, err
		}

		readings = append(readings, &reading)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return readings, nil
}
