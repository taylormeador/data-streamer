package main

import (
	"net/http"
	"strconv"
	"time"

	"github.com/taylormeador/data-streamer/analytics-api/internal/data"
)

// Writes aggregate statistics for all devices in the system.
func (app *application) getDevicesHandler(w http.ResponseWriter, r *http.Request) {
	activeOnly := r.URL.Query().Get("active") == "true"

	limit := 50 // default
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if parsedLimit, err := strconv.Atoi(limitStr); err == nil && parsedLimit > 0 {
			limit = parsedLimit
		}
	}

	devices, err := app.models.Devices.GetAllDevices(r.Context(), activeOnly, limit)
	if err != nil {
		app.serverErrorResponse(w, r, err)
		return
	}

	err = app.writeJSON(w, http.StatusOK, envelope{"devices": devices}, nil)
	if err != nil {
		app.serverErrorResponse(w, r, err)
	}
}

// Retrieve the interpolated "id" parameter from the current URL and include
// it in a placeholder response.
func (app *application) getDeviceHandler(w http.ResponseWriter, r *http.Request) {
	id, err := app.readIDParam(r)
	if err != nil {
		app.notFoundResponse(w, r)
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
		app.serverErrorResponse(w, r, err)
	}
}
