package main

import (
	"net/http"
)

// Writes information about the application status, operating environment and version.
func (app *application) systemHealthHandler(w http.ResponseWriter, r *http.Request) {
	data := map[string]string{
		"status":      "available",
		"environment": app.config.env,
		"version":     version,
	}

	err := app.writeJSON(w, http.StatusOK, data, nil)
	if err != nil {
		app.logger.Error(err.Error())
		http.Error(w, "The server encountered a problem and could not process your request", http.StatusInternalServerError)
	}
}

// Writes system-wide statistics and metrics.
func (app *application) systemStatsHandler(w http.ResponseWriter, r *http.Request) {
	data := map[string]string{
		"total_readings":  "TODO",
		"unique_devices":  "TODO",
		"total_anomalies": "TODO",
		"latest_reading":  "TODO",
	}

	err := app.writeJSON(w, http.StatusOK, data, nil)
	if err != nil {
		app.logger.Error(err.Error())
		http.Error(w, "The server encountered a problem and could not process your request", http.StatusInternalServerError)
	}
}
