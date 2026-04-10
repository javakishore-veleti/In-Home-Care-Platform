# slack_channel_responder_flow

LangGraph workflow that watches configured Slack channels (`#field-ops`, `#customer-support`, `#care-admin`). Classifies each message, retrieves grounded context from VectorDB (policies, runbooks, past tickets, past threads), calls the LLM, and replies in-thread with cited sources. Escalates to a human when no grounded answer is available.

**Tech:** LangGraph, slack-bolt, slack-sdk, LangChain retriever, LlmClient Protocol, VectorClient Protocol, PyMongo, Pytest.
