package main

import (
	"net/http"
	"strconv"
	"time"
)

// Handles GET /readings - returns recent readings across all devices.
func (app *application) getReadingsHandler(w http.ResponseWriter, r *http.Request) {
	// Parse metric filter
	metric := r.URL.Query().Get("metric")

	// Parse anomaly filter
	anomalyOnly := r.URL.Query().Get("anomaly") == "true"

	// Parse start time
	var start *time.Time
	if startStr := r.URL.Query().Get("start"); startStr != "" {
		parsedStart, err := time.Parse(time.RFC3339, startStr)
		if err != nil {
			app.badRequestResponse(w, r, err)
			return
		}
		start = &parsedStart
	}

	// Parse end time
	var end *time.Time
	if endStr := r.URL.Query().Get("end"); endStr != "" {
		parsedEnd, err := time.Parse(time.RFC3339, endStr)
		if err != nil {
			app.badRequestResponse(w, r, err)
			return
		}
		end = &parsedEnd
	}

	// Parse limit
	limit := 100 // default
	if limitStr := r.URL.Query().Get("limit"); limitStr != "" {
		if parsedLimit, err := strconv.Atoi(limitStr); err == nil && parsedLimit > 0 {
			limit = parsedLimit
		}
	}

	// Parse offset
	offset := 0
	if offsetStr := r.URL.Query().Get("offset"); offsetStr != "" {
		if parsedOffset, err := strconv.Atoi(offsetStr); err == nil && parsedOffset >= 0 {
			offset = parsedOffset
		}
	}

	readings, err := app.models.Readings.GetReadings(r.Context(), metric, anomalyOnly, start, end, limit, offset)
	if err != nil {
		app.serverErrorResponse(w, r, err)
		return
	}

	err = app.writeJSON(w, http.StatusOK, envelope{"readings": readings}, nil)
	if err != nil {
		app.serverErrorResponse(w, r, err)
	}
}

// Handles GET /readings/latest - returns the most recent reading for each device.
func (app *application) getLatestReadingsHandler(w http.ResponseWriter, r *http.Request) {
	// Parse metric filter
	metric := r.URL.Query().Get("metric")

	// Parse active_only filter (only devices seen recently)
	activeOnly := r.URL.Query().Get("active") == "true"

	readings, err := app.models.Readings.GetLatestReadings(r.Context(), metric, activeOnly)
	if err != nil {
		app.serverErrorResponse(w, r, err)
		return
	}

	err = app.writeJSON(w, http.StatusOK, envelope{"readings": readings, "count": len(readings)}, nil)
	if err != nil {
		app.serverErrorResponse(w, r, err)
	}
}
