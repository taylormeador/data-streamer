package main

import (
    "encoding/json"
    "log"
    "net/http"
    "os"
    "time"
)

type application struct {
    logger *log.Logger
}

func main() {
    logger := log.New(os.Stdout, "", log.Ldate|log.Ltime)

    app := &application{
        logger: logger,
    }

    srv := &http.Server{
        Addr:         ":8003",
        Handler:      app.routes(),
        IdleTimeout:  time.Minute,
        ReadTimeout:  10 * time.Second,
        WriteTimeout: 30 * time.Second,
    }

    logger.Printf("starting analytics API server on %s", srv.Addr)
    err := srv.ListenAndServe()
    logger.Fatal(err)
}

func (app *application) routes() http.Handler {
    mux := http.NewServeMux()

    mux.HandleFunc("GET /health", app.healthCheckHandler)
    mux.HandleFunc("GET /hello", app.helloHandler)

    return mux
}

func (app *application) healthCheckHandler(w http.ResponseWriter, r *http.Request) {
    data := map[string]string{
        "status": "healthy",
        "service": "analytics-api",
    }

    app.writeJSON(w, http.StatusOK, data)
}

func (app *application) helloHandler(w http.ResponseWriter, r *http.Request) {
    data := map[string]string{
        "message": "Hello from Analytics API",
        "version": "1.0.0",
    }

    app.writeJSON(w, http.StatusOK, data)
}

func (app *application) writeJSON(w http.ResponseWriter, status int, data interface{}) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    
    err := json.NewEncoder(w).Encode(data)
    if err != nil {
        app.logger.Println(err)
    }
}