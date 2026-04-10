# auth_svc

Sign up, sign in, and token management. Issues JWTs on successful authentication. Supports four roles: `member` (patients), `field_staff`, `support` (customer support agents), and `admin`. Owns the `users` and `sessions` MongoDB collections.

**Tech:** FastAPI, PyMongo, passlib (bcrypt), python-jose (JWT), Pytest.
