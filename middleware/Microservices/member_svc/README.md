# member_svc

Member (patient) profile CRUD. Stores demographics, contact info, insurance, care preferences, and consent flags. PII-tagged fields are redacted by the structured logger and the MCP gateway. Owns the `members` MongoDB collection.

**Tech:** FastAPI, PyMongo, Pydantic v2 with `json_schema_extra={"pii": True}`, Pytest.
