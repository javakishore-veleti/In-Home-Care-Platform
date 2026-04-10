# visit_ingest_svc

Receives field data from the mobile app after a visit: visit notes, intake forms, care plan updates, photos. Stores raw documents and hands them off to `document_intelligence_svc` for OCR and field extraction. Owns the `visit_documents` MongoDB collection.

**Tech:** FastAPI, PyMongo, file upload (UploadFile), Pytest.
