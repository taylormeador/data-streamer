package main

import (
	"net/http"

	"github.com/julienschmidt/httprouter"
)

func (app *application) routes() http.Handler {
	router := httprouter.New()

	router.HandlerFunc(http.MethodGet, "/v1/system/health", app.systemHealthHandler)
	router.HandlerFunc(http.MethodGet, "/v1/system/stats", app.systemStatsHandler)

	router.HandlerFunc(http.MethodGet, "/v1/devices", app.getDevicesHandler)
	router.HandlerFunc(http.MethodGet, "/v1/devices/:id", app.getDeviceHandler)

	return router
}
