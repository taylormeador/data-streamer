package main

import (
	"net/http"
	"time"

	"github.com/taylormeador/data-streamer/analytics-api/internal/data"
)

// Writes aggregate statistics for all devices in the system.
func (app *application) getDevicesHandler(w http.ResponseWriter, r *http.Request) {
	devices := data.DeviceStats{
		DeviceID:     45,
		MessageCount: 0,
		AvgValue:     0.0,
		LastSeen:     time.Now(),
		AnomalyCount: 0,
	}

	err := app.writeJSON(w, http.StatusOK, envelope{"devices": devices}, nil)
	if err != nil {
		app.logger.Error(err.Error())
		http.Error(w, "The server encountered a problem and could not process your request", http.StatusInternalServerError)
	}
}

// Retrieve the interpolated "id" parameter from the current URL and include
// it in a placeholder response.
func (app *application) getDeviceHandler(w http.ResponseWriter, r *http.Request) {
	id, err := app.readIDParam(r)
	if err != nil {
		http.NotFound(w, r)
		return
	}

	deviceReading := data.DeviceReading{
		ID:              24,
		DeviceID:        id,
		Metric:          "temperature",
		Value:           35.65,
		Timestamp:       time.Now(),
		Location:        "warehouse-a",
		AnomalyDetected: false,
		RollingAvg:      56.7,
		DeviationPct:    10.67,
		ProcessedAt:     time.Now(),
	}

	err = app.writeJSON(w, http.StatusOK, envelope{"device_reading": deviceReading}, nil)
	if err != nil {
		app.logger.Error(err.Error())
		http.Error(w, "The server encountered a problem and could not process your request", http.StatusInternalServerError)
	}
}
