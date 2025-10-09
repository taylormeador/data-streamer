# Real-Time IoT Device Data Streaming Platform

This project explores distributed systems architecture and event-driven design patterns through a simulated IoT data streaming platform. The primary goal is to deepen expertise with Python, Go, Kafka, Redis, PostgreSQL, and containerized microservices. The platform has evolved from a simple monolithic service toward a more sophisticated microservices architecture, documented below.

Each iteration introduces new distributed systems concepts and architectural patterns, demonstrating practical implementations of service communication, caching strategies, data consistency management, and operational complexity in production-like environments.

See [API.md](API.md) for complete endpoint documentation.


### Timeline

| Date     | Architecture Diagram | Performance Results |
|----------|----------------------|---------------------|
| 9-24-25  | [v0 Architecture](#v0-architecture-diagram) | [v0 Results](#v0-performance-results) · [JSON](/performance/v0_results.json) |
| 9-25-25  | [v1 Architecture](#v1-architecture-diagram) | [v1 Results](#v1-performance-results) · [JSON](/performance/v1_results.json) |
| 9-30-25  | [v2 Architecture](#v2-architecture-diagram) | [v2 Results](#v2-performance-results) · [JSON](/performance/v2_results.json) |

---

### Changelog

- **v0 (9-24-25)** — Initial version. Producer API → Kafka → Consumer API. No database. Simple, in-memory real-time metrics + anomaly detection.  
- **v1 (9-25-25)** — Database integration (Postgres) for persistence. Consumer API writes metrics + anomalies to DB with defined schema. Serving analytics endpoints from db queries instead of in-memory data structures.
- **v2 (9-30-25)** — Add Redis with simple read through caching for /analytics and /device-stats endpoints.

### Tentative Roadmap

  - Full REST API in Go for historical + analytics data.
  - Split Consumer API into consumer/processor services, add corresponding Kafka topics.
  - Visualization layer (Grafana). Enhanced anomaly detection. Alerting/notification system.
  - API Gateway (centralized routing, authentication/authorization, rate limiting)
  - Split DB into OLTP/OLAP DBs (Postgres + time series DB e.g. TimescaleDB, InfluxDB) and add ETL batch jobs service.

---

### Architecture Evolution

#### v0 Architecture Diagram


<img width="491" height="571" alt="data-streamer drawio" src="https://github.com/user-attachments/assets/2ca0b08c-0ddc-4d45-904e-ae7a4b5323df" />

#### v1 Architecture Diagram

<img width="551" height="571" alt="data-streamer-v1 drawio(1)" src="https://github.com/user-attachments/assets/7088cca3-14ca-4df1-886b-82b09bf576b1" />

#### v2 Architecture Diagram

<img width="601" height="571" alt="data-streamer-v2 drawio" src="https://github.com/user-attachments/assets/89021d9d-3736-40ab-b6b3-bf502ada297c" />

---

### Benchmark Commands

**Start all services**:
```bash
docker-compose up --build
```

**Run baseline suite** (tests at 25, 100, 250 RPS):
```bash
curl -X POST http://localhost:8002/baseline-suite
```

**Run throughput ceiling test** (incrementally increases load until failure):
```bash
curl -X POST http://localhost:8002/throughput-ceiling
```

**Check benchmark status** (while tests are running):
```bash
curl http://localhost:8002/benchmark-status
```

**Get benchmark results** (JSON format):
```bash
curl http://localhost:8002/benchmark-results
```

**Get markdown-formatted results** (for README):
```bash
curl http://localhost:8002/benchmark-markdown-raw
```

### Notes

- Baseline suite takes approximately 8 minutes to complete
- Throughput ceiling test duration varies based on system performance (5-10 minutes is typical)
- For fresh database state between tests, use `docker-compose down -v` before restarting

---

### Performance Results

These results are collected from the benchmarking service which simulates requests from IoT devices at a predefined rate. While not suitable for rigorous performance analysis, this approach effectively detects major performance changes and validates system functionality as the architecture evolves.

#### v0 Performance Results
| Test Type | Date/Time | Target RPS | Actual RPS | P99 Latency (ms) | Error Rate | Duration (s) |
|-----------|-----------|------------|------------|------------------|------------|-------------|
| light_load | 2025-09-24 14:40 | 25 | 24.9 | 5.6 | 0.0% | 60.3 |
| standard_load | 2025-09-24 14:42 | 100 | 99.4 | 4.9 | 0.0% | 120.0 |
| high_load | 2025-09-24 14:45 | 250 | 247.6 | 4.2 | 0.0% | 60.0 |
| ceiling | 2025-09-24 14:47 | 50 | 49.7 | 4.4 | 0.0% | 45.2 |
| ceiling | 2025-09-24 14:48 | 100 | 99.5 | 4.5 | 0.0% | 45.2 |
| ceiling | 2025-09-24 14:49 | 150 | 149.2 | 4.3 | 0.0% | 45.2 |
| ceiling | 2025-09-24 14:50 | 200 | 199.0 | 4.4 | 0.0% | 45.0 |
| ceiling | 2025-09-24 14:51 | 250 | 248.0 | 4.2 | 0.0% | 45.0 |
| ceiling | 2025-09-24 14:53 | 300 | 294.9 | 4.0 | 0.0% | 45.0 |
| ceiling | 2025-09-24 14:54 | 350 | 325.2 | 4.0 | 0.0% | 45.0 |
| ceiling | 2025-09-24 14:55 | 400 | 345.6 | 3.9 | 0.0% | 45.0 |
| ceiling | 2025-09-24 14:56 | 450 | 367.8 | 3.9 | 0.0% | 45.0 |
| ceiling | 2025-09-24 14:57 | 500 | 364.8 | 3.9 | 0.0% | 45.0 |

#### v1 Performance Results
| Test Type | Date/Time | Target RPS | Actual RPS | P99 Latency (ms) | Error Rate | Duration (s) |
|-----------|-----------|------------|------------|------------------|------------|-------------|
| light_load | 2025-09-25 19:41 | 25 | 24.9 | 4.6 | 0.0% | 60.3 |
| standard_load | 2025-09-25 19:42 | 100 | 99.6 | 4.3 | 0.0% | 120.0 |
| high_load | 2025-09-25 19:45 | 250 | 248.1 | 4.1 | 0.0% | 60.0 |
| ceiling | 2025-09-25 19:20 | 50 | 49.8 | 6.6 | 0.0% | 45.2 |
| ceiling | 2025-09-25 19:21 | 100 | 99.4 | 5.1 | 0.0% | 45.3 |
| ceiling | 2025-09-25 19:23 | 150 | 149.2 | 4.5 | 0.0% | 45.2 |
| ceiling | 2025-09-25 19:24 | 200 | 199.8 | 4.3 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:25 | 250 | 248.4 | 4.4 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:26 | 300 | 297.5 | 4.1 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:27 | 350 | 345.7 | 3.7 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:28 | 400 | 391.9 | 3.7 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:30 | 450 | 438.9 | 3.5 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:31 | 500 | 476.1 | 3.5 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:32 | 550 | 509.2 | 3.3 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:33 | 600 | 565.9 | 3.1 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:34 | 650 | 593.7 | 3.2 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:35 | 700 | 617.4 | 3.1 | 0.0% | 45.0 |
| ceiling | 2025-09-25 19:37 | 750 | 544.2 | 3.2 | 0.0% | 45.0 |

#### v2 Performance Results
| Test Type | Date/Time | Target RPS | Actual RPS | P99 Latency (ms) | Error Rate | Duration (s) |
|-----------|-----------|------------|------------|------------------|------------|-------------|
| individual | 2025-09-30 20:54 | 50 | 49.7 | 10.2 | 0.0% | 30.2 |


I did not run the full benchmarking suite for this iteration because nothing that is put under load by the suite was changed. In the future, I will likely add functionality to the benchmark service which will send requests to the analytics endpoints, but I want to wait until I have a standalone analytics API implemented first.
