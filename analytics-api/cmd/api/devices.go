package main

import (
	"fmt"
	"net/http"
)

// Writes aggregate statistics for all devices in the system.
func (app *application) getDevicesHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, "device_id: TODO")
	fmt.Fprintln(w, "message_count: TODO")
	fmt.Fprintln(w, "avg_value: TODO")
	fmt.Fprintln(w, "last_seen: TODO")
	fmt.Fprintln(w, "anomaly_count: TODO")
}

// Retrieve the interpolated "id" parameter from the current URL and include
// it in a placeholder response.
func (app *application) getDeviceHandler(w http.ResponseWriter, r *http.Request) {
	id, err := app.readIDParam(r)
	if err != nil {
		http.NotFound(w, r)
		return
	}

	fmt.Fprintf(w, "show the details of device %d\n", id)
}
