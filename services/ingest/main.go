package main

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/ab-platform/ingest/handlers"
	kafkapkg "github.com/ab-platform/ingest/kafka"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok", "service": "ingest"})
}

func main() {
	kafkapkg.Init()

	http.HandleFunc("/health", healthHandler)
	http.HandleFunc("/events", handlers.HandleEvent)
	http.Handle("/metrics", promhttp.Handler())

	log.Println("Ingest service listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
