package metrics

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5"
)

type MetricsTracer struct{}

type ContextValue struct {
	key string
}

var query_start = ContextValue{key: "query_start"}

func (t *MetricsTracer) TraceQueryStart(ctx context.Context, conn *pgx.Conn, data pgx.TraceQueryStartData) context.Context {
	// Store start time in context
	return context.WithValue(ctx, query_start, time.Now())
}

func (t *MetricsTracer) TraceQueryEnd(ctx context.Context, conn *pgx.Conn, data pgx.TraceQueryEndData) {
	// Retrieve start time
	start, ok := ctx.Value(query_start.key).(time.Time)
	if !ok {
		return
	}

	duration := time.Since(start).Seconds()

	// Record metrics
	DBQueriesTotal.Inc()
	DBQueryDurationSeconds.Observe(duration)

	// Track errors
	if data.Err != nil && data.Err != pgx.ErrNoRows {
		DBErrorsTotal.Inc()
	}
}
