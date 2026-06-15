FROM golang:alpine AS builder

WORKDIR /app
COPY go.mod .
COPY . .
RUN go build -o ingest .

FROM alpine:3.19
WORKDIR /app
COPY --from=builder /app/ingest .
CMD ["./ingest"]
