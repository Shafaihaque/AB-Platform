package main

import (
	"encoding/json"
	"log"
	"net/http"
)

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ok",
		"service": "ingest",
	})
}

func main() {
	http.HandleFunc("/health", healthHandler)
	log.Println("Ingest service listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
