# knowledge_agent_svc

LLM briefing agent — triggered by appointment.claimed Kafka events.

When a field officer claims an appointment via Slack, this service:
1. Fetches the appointment details (service_type, member_id, date)
2. Calls the RAG search API for the matching knowledge collection
3. Assembles a prompt with RAG context
4. Calls the configured LLM (Ollama/OpenAI/Groq via OpenAI-compatible API)
5. Posts the briefing as a Slack threaded reply under the claimed message

**Port**: 8011

## Configuration

| Env var | Default | Description |
|---|---|---|
| `LLM_API_BASE` | `http://localhost:11434/v1` | OpenAI-compatible base URL (Ollama default) |
| `LLM_MODEL` | `llama3` | Model ID |
| `LLM_API_KEY` | empty | API key (not needed for Ollama) |
| `LLM_MAX_TOKENS` | `1024` | Max output tokens |
| `LLM_TEMPERATURE` | `0.3` | Sampling temperature |
| `APPOINTMENT_SVC_URL` | `http://127.0.0.1:8004` | appointment_svc base URL |
| `API_GATEWAY_URL` | `http://127.0.0.1:8001` | api_gateway base URL (for RAG search) |

## Using with OpenAI instead of Ollama

```bash
# In .env.local:
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...
```

## Using with Ollama (default, free)

```bash
# Install Ollama: https://ollama.com/download
ollama pull llama3
# Service auto-connects to http://localhost:11434/v1
```
