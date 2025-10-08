package database

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Connect to database.
func Open(dsn string) (*pgxpool.Pool, error) {
	pool, err := pgxpool.New(context.Background(), dsn)
	if err != nil {
		return nil, err
	}

	// Verify database connection
	err = pool.Ping(context.Background())
	if err != nil {
		pool.Close()
		return nil, err
	}

	return pool, nil
}
