package main

import (
	"fmt"
	"net/http"
	"strconv"
	"time"

	"github.com/taylormeador/data-streamer/analytics-api/internal/metrics"
)

func (app *application) recoverPanic(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			pv := recover()
			if pv != nil {
				w.Header().Set("Connection", "close")
				app.serverErrorResponse(w, r, fmt.Errorf("%v", pv))
			}
		}()

		next.ServeHTTP(w, r)
	})
}

// captureMetrics wraps handlers to record metrics
func (app *application) captureMetrics(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Wrap ResponseWriter to capture status code
		wrapped := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		// Call the next handler
		next.ServeHTTP(wrapped, r)

		// Record metrics
		duration := time.Since(start).Seconds()
		endpoint := r.URL.Path
		method := r.Method
		status := strconv.Itoa(wrapped.statusCode)

		metrics.HttpRequestsTotal.WithLabelValues(method, endpoint, status).Inc()
		metrics.HttpRequestDuration.WithLabelValues(method, endpoint).Observe(duration)
	})
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}
