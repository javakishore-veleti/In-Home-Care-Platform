# document_author_flow

LangGraph workflow that drafts visit summaries from extracted fields + past visit context. Triggered after `document_intelligence_svc` processes a new visit document. The draft is presented for staff review via the admin portal or Slack. Uses VectorDB for similar past summaries and the LLM for composition.

**Tech:** LangGraph, LlmClient Protocol, VectorClient Protocol, PyMongo, Pytest.
