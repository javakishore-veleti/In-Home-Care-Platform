# appointment_svc

Book, cancel, and reschedule appointments. Validates service area + availability. On booking, publishes an `appointment.booked` Kafka event that `visit_management_svc` consumes to create a pending visit. Owns the `appointments` MongoDB collection.

**Tech:** FastAPI, PyMongo, aiokafka (or in-memory bus), Pytest.
