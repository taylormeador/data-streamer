package main

import (
	"net/http"

	"github.com/julienschmidt/httprouter"
)

func (app *application) routes() http.Handler {
	router := httprouter.New()

	router.NotFound = http.HandlerFunc(app.notFoundResponse)
	router.MethodNotAllowed = http.HandlerFunc(app.methodNotAllowedResponse)

	// System endpoints
	router.HandlerFunc(http.MethodGet, "/v1/system/health", app.systemHealthHandler)
	router.HandlerFunc(http.MethodGet, "/v1/system/stats", app.systemStatsHandler)

	// Device endpoints
	router.HandlerFunc(http.MethodGet, "/v1/devices", app.getDevicesHandler)
	router.HandlerFunc(http.MethodGet, "/v1/devices/:id", app.getDeviceHandler)
	router.HandlerFunc(http.MethodGet, "/v1/devices/:id/readings", app.getDeviceReadingsHandler)
	router.HandlerFunc(http.MethodGet, "/v1/devices/:id/anomalies", app.getDeviceAnomaliesHandler)

	// Readings endpoints
	router.HandlerFunc(http.MethodGet, "/v1/readings", app.getReadingsHandler)
	router.HandlerFunc(http.MethodGet, "/v1/readings/latest", app.getLatestReadingsHandler)

	return app.recoverPanic(router)
}
