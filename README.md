# AB Platform

A self-serve A/B experimentation platform. Any app can plug into it to run experiments, define variants, consistently assign users, ingest events at scale, and view important results in real time.


## Running Locally

This project uses a **hybrid dev setup**: infrastructure runs in Docker, application services run locally for fast hot reload.

### 1. Start infrastructure

```bash
docker compose up -d
```

This starts: Postgres, ClickHouse, Redis, Kafka, and Zookeeper.

### 2. Run the API (FastAPI)

```bash
cd services/api
pip install -r requirements.txt
uvicorn main:app --reload
```

API available at http://localhost:8000

### 3. Run the ingest service (Go)

```bash
cd services/ingest
go run main.go
```

Ingest service available at http://localhost:8080

### 4. Run the frontend (React)

```bash
cd frontend
npm install
npm run dev
```

Frontend available at http://localhost:5173

### Infrastructure ports

| Service    | Port |
|------------|------|
| Postgres   | 5432 |
| ClickHouse | 8123 |
| Redis      | 6379 |
| Kafka      | 9092 |

### Stop infrastructure

```bash
docker compose down
```
