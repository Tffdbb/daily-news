# Simple Go Load Balancer

Round-robin load balancer written in Go. Starter project for daily-news.

## Quick Start

```bash
# 1. Start 3 test backends
python3 -m http.server 8081 &
python3 -m http.server 8082 &
python3 -m http.server 8083 &

# 2. Run the load balancer
go run main.go

# 3. Send requests - they get distributed
curl http://localhost:8080
```

## What you learn

- Go net/http reverse proxy
- Atomic operations for round-robin
- Mutex-protected state
- TCP health checks
- Goroutine background tasks