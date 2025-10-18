// internal/metrics/metrics.go
package metrics

import (
	"fmt"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

const prefix string = "ANALYTICS"

var (
	HttpRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: fmt.Sprintf("%s_http_requests_total", prefix),
			Help: "Total HTTP requests",
		},
		[]string{"method", "endpoint", "status"},
	)

	HttpRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name: fmt.Sprintf("%s_http_request_duration_seconds", prefix),
			Help: "HTTP request duration",
		},
		[]string{"method", "endpoint"},
	)

	CacheHits = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: fmt.Sprintf("%s_cache_hits_total", prefix),
			Help: "Total cache hits",
		},
	)

	CacheMisses = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: fmt.Sprintf("%s_cache_misses_total", prefix),
			Help: "Total cache misses",
		},
	)

	DBQueriesTotal = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: fmt.Sprintf("%s_db_queries_total", prefix),
			Help: "Total DB queries",
		},
	)

	DBQueryDurationSeconds = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name: fmt.Sprintf("%s_db_query_duration_seconds", prefix),
			Help: "DB query duration",
		},
	)

	DBErrorsTotal = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: fmt.Sprintf("%s_db_errors_total", prefix),
			Help: "Total DB errors",
		},
	)
)
