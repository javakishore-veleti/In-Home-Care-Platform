# kafka

Docker Compose stack for local Kafka. Used by `appointment_svc` (publish) and `visit_management_svc` (consume) for event-driven communication.

```bash
docker compose up -d
```

Default broker: `localhost:9092`
