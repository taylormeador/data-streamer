package main

import (
	"errors"
	"net/http"
	"strconv"

	"github.com/jackc/pgx/v5"
	"github.com/julienschmidt/httprouter"
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
	id := params.ByName("id")

	device, err := app.models.Devices.GetDevice(r.Context(), id)
	if err != nil {
		switch {
		case errors.Is(err, pgx.ErrNoRows):
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
