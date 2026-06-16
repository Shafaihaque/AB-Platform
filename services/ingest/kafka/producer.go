package kafka

import (
	"context"
	"encoding/json"
	"os"
	"time"

	kafka "github.com/segmentio/kafka-go"
)

// Writer is the shared Kafka producer — kept open for the lifetime of the app.
var Writer *kafka.Writer

// Init creates the Kafka writer on startup.
func Init() {
	brokers := os.Getenv("KAFKA_BROKERS")
	if brokers == "" {
		brokers = "localhost:9092"
	}

	Writer = &kafka.Writer{
		Addr:         kafka.TCP(brokers),
		Topic:        "ab.events",
		Balancer:     &kafka.LeastBytes{},
		WriteTimeout: 5 * time.Second,
	}
}

// Publish serializes an event to JSON and writes it to the Kafka topic.
func Publish(ctx context.Context, event any) error {
	data, err := json.Marshal(event)
	if err != nil {
		return err
	}
	return Writer.WriteMessages(ctx, kafka.Message{Value: data})
}
