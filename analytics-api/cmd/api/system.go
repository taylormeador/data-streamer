package main

import (
	"context"
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
	systemStats, err := app.models.System.GetSystemStats(context.Background())
	if err != nil {
		app.serverErrorResponse(w, r, err)
		return
	}

	err = app.writeJSON(w, http.StatusOK, envelope{"system_stats": systemStats}, nil)
	if err != nil {
		app.serverErrorResponse(w, r, err)
	}
}
