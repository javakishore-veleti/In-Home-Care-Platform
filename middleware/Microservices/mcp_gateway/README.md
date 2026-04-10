# mcp_gateway

FastMCP + Google ADK gateway exposing microservice capabilities as MCP tools to LLM clients. Tools include `member_lookup`, `visit_history`, `appointment_status`, `document_search`. Token auth + per-tool scope enforcement + immutable audit log per call. The LangGraph agentic flows call these tools to ground their answers.

**Tech:** FastMCP, Google ADK (LlmAgent + Runner), FastAPI, PyMongo, structlog, Pytest.
