# api_gateway

FastAPI gateway — the single entry point for all portal and mobile app traffic. Routes requests to downstream microservices, verifies JWT tokens from `auth_svc`, enforces role-based access (`member`, `field_staff`, `support`, `admin`), and applies rate limiting. Owns no collections; talks to every service.

**Tech:** FastAPI, pydantic-settings, structlog, Pytest.
