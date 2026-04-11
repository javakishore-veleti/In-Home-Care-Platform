"""Internal-only endpoints used by other services in the local stack.

These routes are deliberately *not* gated by JWT — they're called by
sibling services (e.g. slack_svc → /api/internal/slack/integrations/lookup)
that don't carry user credentials. The data exposed here is intentionally
small and harmless: a (event_type → channel) lookup, no PII.

If/when this stack runs in an environment where the api_gateway is
exposed publicly, these routes should be moved behind a private listener
or guarded by a static internal token. For local dev, no auth is fine.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from .dependencies import get_slack_integration_store

router = APIRouter(prefix='/api/internal', tags=['internal'])


@router.get('/slack/integrations/lookup')
def lookup_slack_integration(
    event_type: str,
    slack_integration_store=Depends(get_slack_integration_store),
) -> dict[str, Any]:
    """Return *all* active integrations for an event_type.

    Response shape: ``{integrations: [{slack_channel_id, slack_channel_name, ...}, ...]}``.
    Empty list means no rows were configured — slack_svc treats that as
    "use the env-var default channel".
    """
    integrations = slack_integration_store.list_enabled_for_event(event_type)
    return {'integrations': integrations}
