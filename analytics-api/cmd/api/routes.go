package main

import (
	"net/http"

	"github.com/julienschmidt/httprouter"
)

func (app *application) routes() http.Handler {
	router := httprouter.New()

	router.HandlerFunc(http.MethodGet, "/v1/system/health", app.systemHealthHandler)
	router.HandlerFunc(http.MethodGet, "/v1/system/stats", app.systemStatsHandler)

	return router
}
