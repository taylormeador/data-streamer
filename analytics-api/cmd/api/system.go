package main

import (
	"fmt"
	"net/http"
)

// Writes information about the application status, operating environment and version.
func (app *application) systemHealthHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, "status: available")
	fmt.Fprintf(w, "environment: %s\n", app.config.env)
	fmt.Fprintf(w, "version: %s\n", version)
}

// Writes system-wide statistics and metrics.
func (app *application) systemStatsHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, "total_readings: TODO")
	fmt.Fprintln(w, "unique_devices: TODO")
}
