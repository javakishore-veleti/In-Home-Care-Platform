# visit_intelligence_flow

LangGraph workflow triggered on visit completion. Scores the visit data against the member's longitudinal record, detects care gaps and follow-up tasks, and writes dispositions. Uses VectorDB for similar-case retrieval and the LLM for reasoning. Invokes microservice tools via the MCP gateway.

**Tech:** LangGraph, LangChain retriever, LlmClient Protocol, VectorClient Protocol, PyMongo, Pytest.
