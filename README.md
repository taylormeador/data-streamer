# Real-Time IoT Device Data Streaming Platform

This project is a prototype of a distributed, high-throughput data streaming platform for IoT device data.  

The goal is not to build a production-ready system, but to explore how distributed architectures evolve as they scale. Each iteration introduces new features, realistic business logic, and simulated product requirements. As the system grows more complex, I’ll benchmark performance, document results, and use the findings to identify bottlenecks and experiment with optimizations.

Over time, additional services will be introduced and existing ones scaled horizontally, while resource usage per service will remain consistent through fixed limits in Docker Compose. The focus is on understanding how distributed systems behave under load, how design trade-offs emerge, and how architectures adapt across the lifecycle of a project.


### Timeline

| Date     | Architecture Diagram | Performance Results |
|----------|----------------------|---------------------|
| TBD      | [v0 Architecture](/performance/v0_architecture) | [v0 Results](#v0-performance-results) · [JSON](/performance/v0_results.json) |

---

### Changelog

- **v0 (TBD)** — Initial version. Producer API → Kafka → Consumer API. No database. Simple, in-memory real-time metrics + anomaly detection.  
- **v1 (TBD)** — Database integration (Postgres) for persistence. Consumer API writes metrics + anomalies to DB with defined schema. REST API for querying historical data.
- **v2 (TBD)** — Visualization layer (Grafana). Enhanced anomaly detection. Alerting/notification system.
- **v3 (TBD)** — Scalable deployment. Multiple consumer groups + partitioning for high throughput.
- **v4 (TBD)** — Rewrite APIs in Go.

---

### Performance Results

#### v0 Performance Results
*(Coming soon)*
