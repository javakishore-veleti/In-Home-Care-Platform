"""S3 source adapter for knowledge repositories.

When a repository's source_mode is 's3', the indexing pipeline
reads files from an S3 bucket instead of the local filesystem.
Uses boto3 — requires AWS credentials configured via env or
~/.aws/credentials.

Config via env:
  KNOWLEDGE_S3_BUCKET    default: ihcp-knowledge-prod
  AWS_REGION             default: us-east-1
  AWS_ACCESS_KEY_ID      (or use IAM role / instance profile)
  AWS_SECRET_ACCESS_KEY
"""
from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)

S3_BUCKET = os.getenv('KNOWLEDGE_S3_BUCKET', 'ihcp-knowledge-prod')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')


def list_s3_files(prefix: str) -> list[dict[str, Any]]:
    """List all files under an S3 prefix.

    Returns [{key, size, last_modified}, ...].
    """
    try:
        import boto3
    except ImportError:
        log.error('s3_adapter.boto3_not_installed — pip install boto3')
        return []

    s3 = boto3.client('s3', region_name=AWS_REGION)
    files: list[dict[str, Any]] = []
    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj.get('Key', '')
            if key.endswith('/'):
                continue
            files.append({
                'key': key,
                'size': obj.get('Size', 0),
                'last_modified': str(obj.get('LastModified', '')),
                'filename': key.rsplit('/', 1)[-1] if '/' in key else key,
            })

    log.info('s3_adapter.listed bucket=%s prefix=%s files=%d', S3_BUCKET, prefix, len(files))
    return files


def read_s3_file(key: str) -> bytes:
    """Read the contents of a single S3 object."""
    try:
        import boto3
    except ImportError:
        log.error('s3_adapter.boto3_not_installed')
        return b''

    s3 = boto3.client('s3', region_name=AWS_REGION)
    resp = s3.get_object(Bucket=S3_BUCKET, Key=key)
    data = resp['Body'].read()
    log.info('s3_adapter.read key=%s size=%d', key, len(data))
    return data


def read_s3_text(key: str, encoding: str = 'utf-8') -> str:
    """Read an S3 object as decoded text."""
    return read_s3_file(key).decode(encoding, errors='replace')
