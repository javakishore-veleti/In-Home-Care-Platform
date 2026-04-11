"""Shared aiokafka producer + consumer helpers.

Why this module exists
----------------------
Producers and consumers across services need consistent broker config,
JSON serialization, and graceful degradation when Kafka isn't running
locally. Centralizing here keeps each service's main.py small and avoids
divergent retry/serialization rules.

The producer is a process-singleton started lazily on the first publish
and torn down via stop_producer() in the FastAPI lifespan handler.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Awaitable, Callable

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
    from aiokafka.errors import KafkaError
    from aiokafka.structs import OffsetAndMetadata
except Exception:  # pragma: no cover
    AIOKafkaConsumer = None  # type: ignore[assignment]
    AIOKafkaProducer = None  # type: ignore[assignment]
    KafkaError = Exception  # type: ignore[assignment,misc]
    OffsetAndMetadata = None  # type: ignore[assignment]

log = logging.getLogger(__name__)

_producer: 'AIOKafkaProducer | None' = None
_producer_lock = asyncio.Lock()


def bootstrap_servers() -> str:
    return os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')


def kafka_enabled() -> bool:
    if AIOKafkaProducer is None:
        return False
    return os.getenv('KAFKA_DISABLED', '').lower() not in {'1', 'true', 'yes'}


async def get_producer() -> 'AIOKafkaProducer | None':
    """Lazy-start the singleton producer. Returns None if Kafka is disabled or unreachable."""
    global _producer
    if not kafka_enabled():
        return None
    if _producer is not None:
        return _producer
    async with _producer_lock:
        if _producer is not None:
            return _producer
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=bootstrap_servers(),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda v: v.encode('utf-8') if isinstance(v, str) else v,
                acks='all',
                enable_idempotence=True,
                request_timeout_ms=5000,
            )
            await producer.start()
            _producer = producer
            log.info('kafka.producer_started', extra={'bootstrap': bootstrap_servers()})
        except (KafkaError, OSError) as exc:
            log.warning('kafka.producer_start_failed', extra={'error': str(exc)})
            return None
    return _producer


async def publish(topic: str, *, value: dict[str, Any], key: str | None = None) -> bool:
    """Publish a JSON event. Returns True on success, False on any failure (logged)."""
    producer = await get_producer()
    if producer is None:
        log.info('kafka.publish_skipped', extra={'topic': topic, 'reason': 'no_producer'})
        return False
    try:
        await producer.send_and_wait(topic, value=value, key=key)
        return True
    except (KafkaError, OSError) as exc:
        log.warning('kafka.publish_failed', extra={'topic': topic, 'error': str(exc)})
        return False


async def stop_producer() -> None:
    global _producer
    if _producer is not None:
        try:
            await _producer.stop()
        finally:
            _producer = None


async def run_consumer(
    *,
    topic: str,
    group_id: str,
    handler: Callable[[dict[str, Any]], Awaitable[bool]],
    stop_event: asyncio.Event,
) -> None:
    """Consume `topic` and dispatch each JSON message to `handler`.

    The handler returns True to commit the offset (success or terminal skip)
    or False to leave the offset uncommitted so Kafka redelivers on the next
    poll. The loop reconnects on broker errors with exponential backoff so a
    Kafka outage at startup does not crash the service.
    """
    if AIOKafkaConsumer is None or not kafka_enabled():
        log.warning('kafka.consumer_disabled', extra={'topic': topic, 'group_id': group_id})
        return

    backoff = 1.0
    while not stop_event.is_set():
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers(),
            group_id=group_id,
            enable_auto_commit=False,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='earliest',
        )
        try:
            await consumer.start()
            backoff = 1.0
            log.info('kafka.consumer_started', extra={'topic': topic, 'group_id': group_id})
            while not stop_event.is_set():
                batch = await consumer.getmany(timeout_ms=1000, max_records=10)
                rewind_after_batch = False
                for tp, msgs in batch.items():
                    last_ok_offset: int | None = None
                    rewind_to: int | None = None
                    for msg in msgs:
                        try:
                            ok = await handler(msg.value)
                        except Exception as exc:  # pragma: no cover
                            log.exception('kafka.handler_error', extra={'error': str(exc), 'topic': topic})
                            ok = False
                        if ok:
                            last_ok_offset = msg.offset + 1
                        else:
                            rewind_to = msg.offset
                            break
                    if last_ok_offset is not None and OffsetAndMetadata is not None:
                        await consumer.commit({tp: OffsetAndMetadata(last_ok_offset, '')})
                    if rewind_to is not None:
                        consumer.seek(tp, rewind_to)
                        rewind_after_batch = True
                if rewind_after_batch:
                    # Backoff before the next poll re-delivers the failed message.
                    await asyncio.sleep(2.0)
        except (KafkaError, OSError) as exc:
            log.warning('kafka.consumer_error', extra={'topic': topic, 'error': str(exc), 'backoff': backoff})
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)
        finally:
            try:
                await consumer.stop()
            except Exception:  # pragma: no cover
                pass
