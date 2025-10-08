package main

import (
	"net/http"

	"github.com/taylormeador/data-streamer/analytics-api/internal/data"
)

// Writes information about the application status, operating environment and version.
func (app *application) systemHealthHandler(w http.ResponseWriter, r *http.Request) {
	systemHealth := data.SystemHealth{
		Status:      "available",
		Environment: app.config.env,
		Version:     version,
	}

	err := app.writeJSON(w, http.StatusOK, envelope{"system_health": systemHealth}, nil)
	if err != nil {
		app.serverErrorResponse(w, r, err)
	}
}

// Writes system-wide statistics and metrics.
func (app *application) systemStatsHandler(w http.ResponseWriter, r *http.Request) {
	systemStats := data.SystemStats{
		TotalReadings:  0,
		UniqueDevices:  50,
		TotalAnomalies: 30,
		LatestReading:  nil,
	}

	err := app.writeJSON(w, http.StatusOK, envelope{"system_stats": systemStats}, nil)
	if err != nil {
		app.serverErrorResponse(w, r, err)
	}
}
