package main

import (
	"errors"
	"net/http"
	"strconv"
	"time"

	"github.com/julienschmidt/httprouter"
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

// Retrieve the interpolated "id" parameter from the current URL and write stats for the associated device.
func (app *application) getDeviceHandler(w http.ResponseWriter, r *http.Request) {
	params := httprouter.ParamsFromContext(r.Context())
	deviceID := params.ByName("id")

	device, err := app.models.Devices.GetDevice(r.Context(), deviceID)
	if err != nil {
		switch {
		case errors.Is(err, data.ErrRecordNotFound):
			app.notFoundResponse(w, r)
		default:
			app.serverErrorResponse(w, r, err)
		}
		return
	}

	err = app.writeJSON(w, http.StatusOK, envelope{"device": device}, nil)
	if err != nil {
		app.serverErrorResponse(w, r, err)
	}
}

// Handles GET /devices/{id}/readings - returns historical readings for a device.
func (app *application) getDeviceReadingsHandler(w http.ResponseWriter, r *http.Request) {

	// Parse path parameter
	params := httprouter.ParamsFromContext(r.Context())
	deviceID := params.ByName("id")

	// Parse query parameters
	metric := r.URL.Query().Get("metric")

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

	readings, err := app.models.Devices.GetDeviceReadings(r.Context(), deviceID, metric, start, end, limit)
	if err != nil {
		app.serverErrorResponse(w, r, err)
		return
	}

	err = app.writeJSON(w, http.StatusOK, envelope{"readings": readings}, nil)
	if err != nil {
		app.serverErrorResponse(w, r, err)
	}
}
