# document_intelligence_svc

Wraps GCP Document AI for OCR and form field extraction. Receives raw documents from `visit_ingest_svc`, runs the appropriate processor (intake form / visit note / care plan), normalizes and validates the extracted fields, and stores them. Owns the `extracted_fields` MongoDB collection.

**Tech:** FastAPI, GCP Document AI SDK, PyMongo, Pytest + MagicMock (mock Doc AI in tests).
