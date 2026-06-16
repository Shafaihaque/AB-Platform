package handlers

import (
	"encoding/json"
	"net/http"
	"time"

	kafkapkg "github.com/ab-platform/ingest/kafka"
)

type Event struct {
	ExperimentID string `json:"experiment_id"`
	VariantID    string `json:"variant_id"`
	UserID       string `json:"user_id"`
	EventType    string `json:"event_type"`
	Timestamp    string `json:"timestamp"`
}

// writeJSON sends a JSON response with the given status code.
func writeJSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// HandleEvent validates the incoming event and publishes it to Kafka.
func HandleEvent(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, map[string]string{"error": "method not allowed"})
		return
	}

	var event Event
	if err := json.NewDecoder(r.Body).Decode(&event); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON"})
		return
	}

	if event.ExperimentID == "" || event.VariantID == "" || event.UserID == "" || event.EventType == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "missing required fields"})
		return
	}

	if event.Timestamp == "" {
		event.Timestamp = time.Now().UTC().Format(time.RFC3339)
	}

	if err := kafkapkg.Publish(r.Context(), event); err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "failed to publish event"})
		return
	}

	writeJSON(w, http.StatusAccepted, map[string]string{"status": "accepted"})
}
