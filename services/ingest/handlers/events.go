package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	kafkapkg "github.com/ab-platform/ingest/kafka"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	httpRequests = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "ab_ingest_http_requests_total",
			Help: "Total event-ingestion HTTP requests by response status.",
		},
		[]string{"status"},
	)
	httpRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "ab_ingest_http_request_duration_seconds",
			Help:    "Event-ingestion HTTP request duration by response status.",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"status"},
	)
	kafkaPublishDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "ab_ingest_kafka_publish_duration_seconds",
			Help:    "Time spent publishing an event to Kafka.",
			Buckets: prometheus.DefBuckets,
		},
	)
	kafkaPublishErrors = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "ab_ingest_kafka_publish_errors_total",
			Help: "Total failed Kafka event publishes.",
		},
	)
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
	requestStarted := time.Now()
	status := http.StatusInternalServerError
	defer func() {
		statusLabel := strconv.Itoa(status)
		httpRequests.WithLabelValues(statusLabel).Inc()
		httpRequestDuration.WithLabelValues(statusLabel).Observe(time.Since(requestStarted).Seconds())
	}()

	if r.Method != http.MethodPost {
		status = http.StatusMethodNotAllowed
		writeJSON(w, status, map[string]string{"error": "method not allowed"})
		return
	}

	var event Event
	if err := json.NewDecoder(r.Body).Decode(&event); err != nil {
		status = http.StatusBadRequest
		writeJSON(w, status, map[string]string{"error": "invalid JSON"})
		return
	}

	if event.ExperimentID == "" || event.VariantID == "" || event.UserID == "" || event.EventType == "" {
		status = http.StatusBadRequest
		writeJSON(w, status, map[string]string{"error": "missing required fields"})
		return
	}

	if event.Timestamp == "" {
		event.Timestamp = time.Now().UTC().Format(time.RFC3339)
	}

	publishStarted := time.Now()
	err := kafkapkg.Publish(r.Context(), event)
	kafkaPublishDuration.Observe(time.Since(publishStarted).Seconds())
	if err != nil {
		kafkaPublishErrors.Inc()
		status = http.StatusInternalServerError
		writeJSON(w, status, map[string]string{"error": "failed to publish event"})
		return
	}

	status = http.StatusAccepted
	writeJSON(w, status, map[string]string{"status": "accepted"})
}
