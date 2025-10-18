package database

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/taylormeador/data-streamer/analytics-api/internal/metrics"
)

// Connect to database.
func Open(dsn string) (*pgxpool.Pool, error) {
	// Parse config from connection string
	config, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, err
	}

	// Configure connection pool
	config.MaxConns = 25
	config.MinConns = 2
	config.MaxConnLifetime = 30 * time.Minute

	// Register metrics tracer
	config.ConnConfig.Tracer = &metrics.MetricsTracer{}

	// Create pool with config
	pool, err := pgxpool.NewWithConfig(context.Background(), config)
	if err != nil {
		return nil, err
	}

	// Verify connection
	err = pool.Ping(context.Background())
	if err != nil {
		pool.Close()
		return nil, err
	}

	return pool, nil
}
