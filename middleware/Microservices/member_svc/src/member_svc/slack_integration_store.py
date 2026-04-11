"""Store for slack_channel_integrations.

Owns the runtime (event_type → Slack channel) mapping that powers the
admin portal's Slack Integrations page. slack_svc reads from here via
the api_gateway internal route to pick the destination channel for each
appointment.events message — falling back to the env var default when
no integration row exists.
"""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from shared.storage import BaseStore, now_utc


class SlackIntegrationStore(BaseStore):
    def __init__(self) -> None:
        super().__init__('slack_integration')

    def list_integrations(self, *, event_type: str | None = None) -> list[dict[str, Any]]:
        if self.using_db:
            params: list[Any] = []
            where_sql = ''
            if event_type:
                where_sql = 'WHERE event_type = %s'
                params.append(event_type)
            return self.fetch_all(
                f'''
                SELECT id, slack_channel_id, slack_channel_name, event_type, enabled,
                       created_at, updated_at
                FROM member_schema.slack_channel_integrations
                {where_sql}
                ORDER BY event_type, slack_channel_name
                ''',
                tuple(params),
            )
        rows = self.memory.list(self._memory_key('integrations'))
        if event_type:
            rows = [row for row in rows if row.get('event_type') == event_type]
        return sorted(rows, key=lambda row: (row.get('event_type', ''), row.get('slack_channel_name', '')))

    def list_enabled_for_event(self, event_type: str) -> list[dict[str, Any]]:
        """Return *every* enabled integration row for ``event_type``.

        slack_svc fans the message out to every row in this list,
        deduping per (appointment_id, channel_id) so a Kafka redelivery
        never re-posts to a channel it already hit.
        """
        if self.using_db:
            return self.fetch_all(
                '''
                SELECT id, slack_channel_id, slack_channel_name, event_type, enabled,
                       created_at, updated_at
                FROM member_schema.slack_channel_integrations
                WHERE event_type = %s AND enabled = TRUE
                ORDER BY id ASC
                ''',
                (event_type,),
            )
        return [
            row
            for row in self.memory.list(self._memory_key('integrations'))
            if row.get('event_type') == event_type and row.get('enabled', True)
        ]

    def upsert_integration(
        self,
        *,
        slack_channel_id: str,
        slack_channel_name: str,
        event_type: str,
    ) -> dict[str, Any]:
        """Create or refresh the (channel, event_type) mapping."""
        if self.using_db:
            row = self.fetch_one(
                '''
                INSERT INTO member_schema.slack_channel_integrations (
                    slack_channel_id, slack_channel_name, event_type, enabled, created_at, updated_at
                )
                VALUES (%s, %s, %s, TRUE, %s, %s)
                ON CONFLICT (slack_channel_id, event_type)
                DO UPDATE SET
                    slack_channel_name = EXCLUDED.slack_channel_name,
                    enabled = TRUE,
                    updated_at = EXCLUDED.updated_at
                RETURNING id, slack_channel_id, slack_channel_name, event_type, enabled,
                          created_at, updated_at
                ''',
                (slack_channel_id, slack_channel_name, event_type, now_utc(), now_utc()),
            )
            assert row is not None
            return row
        existing = next(
            (
                row
                for row in self.memory.list(self._memory_key('integrations'))
                if row.get('slack_channel_id') == slack_channel_id and row.get('event_type') == event_type
            ),
            None,
        )
        if existing:
            updated = self.memory.update(
                self._memory_key('integrations'),
                existing['id'],
                {
                    'slack_channel_name': slack_channel_name,
                    'enabled': True,
                    'updated_at': now_utc(),
                },
            )
            assert updated is not None
            return updated
        return self.memory.insert(
            self._memory_key('integrations'),
            {
                'slack_channel_id': slack_channel_id,
                'slack_channel_name': slack_channel_name,
                'event_type': event_type,
                'enabled': True,
                'created_at': now_utc(),
                'updated_at': now_utc(),
            },
        )

    def set_enabled(self, integration_id: int, enabled: bool) -> dict[str, Any]:
        if self.using_db:
            row = self.fetch_one(
                '''
                UPDATE member_schema.slack_channel_integrations
                SET enabled = %s, updated_at = %s
                WHERE id = %s
                RETURNING id, slack_channel_id, slack_channel_name, event_type, enabled,
                          created_at, updated_at
                ''',
                (enabled, now_utc(), integration_id),
            )
            if not row:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Slack integration not found.')
            return row
        updated = self.memory.update(
            self._memory_key('integrations'),
            integration_id,
            {'enabled': enabled, 'updated_at': now_utc()},
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Slack integration not found.')
        return updated

    def delete_integration(self, integration_id: int) -> None:
        if self.using_db:
            self.execute(
                'DELETE FROM member_schema.slack_channel_integrations WHERE id = %s',
                (integration_id,),
            )
            return
        self.memory.delete(self._memory_key('integrations'), integration_id)
