# knowledge_svc

Knowledge base service — manages collections, repositories, and their
items. Collections are 1:1 with appointment service types. Repositories
sit inside collections and have a lifecycle (draft → locked → publish →
indexed). Items are the individual documents, notes, announcements, etc.

Indexing (chunking + embedding + VectorDB) is handled by Apache Airflow
in Phase 2. This service owns the CRUD and the publish trigger.

**Port**: 8010

```bash
$HOME/runtime_data/python_venvs/In-Home-Care-Platform/bin/uvicorn \
  knowledge_svc.main:app --host 127.0.0.1 --port 8010 \
  --app-dir middleware/Microservices/knowledge_svc/src
```
