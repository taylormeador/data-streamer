package main

import (
	"flag"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"time"

	"github.com/taylormeador/data-streamer/analytics-api/internal/cache"
	"github.com/taylormeador/data-streamer/analytics-api/internal/data"
	"github.com/taylormeador/data-streamer/analytics-api/internal/database"
)

const version = "1.0.0"

type config struct {
	port int
	env  string
}

type application struct {
	config config
	logger *slog.Logger
	models data.Models
	cache  *cache.Cache
}

func main() {
	// Parse config
	var cfg config

	flag.IntVar(&cfg.port, "port", 8003, "API server port")
	flag.StringVar(&cfg.env, "env", "development", "Environment (development|staging|production)")
	flag.Parse()

	logger := slog.New(slog.NewTextHandler(os.Stdout, nil))

	// Connect to database
	db, err := database.Open(os.Getenv("DATABASE_URL"))
	if err != nil {
		logger.Error(err.Error())
		os.Exit(1)
	}
	logger.Info("connected to database")
	defer db.Close()

	// Connect to Redis
	redisCache, err := cache.NewCache(os.Getenv("REDIS_URL"))
	if err != nil {
		logger.Error("failed to connect to redis", "error", err)
		os.Exit(1)
	}
	logger.Info("connected to redis")
	defer redisCache.Close()

	app := &application{
		config: cfg,
		logger: logger,
		models: data.NewModels(db),
		cache:  redisCache,
	}

	// Configure and start server
	srv := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.port),
		Handler:      app.routes(),
		IdleTimeout:  time.Minute,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		ErrorLog:     slog.NewLogLogger(logger.Handler(), slog.LevelError),
	}

	logger.Info("starting server", "addr", srv.Addr, "env", cfg.env)

	err = srv.ListenAndServe()
	logger.Error(err.Error())
	os.Exit(1)
}
