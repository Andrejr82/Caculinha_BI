"""
Compatibility auth helpers for legacy imports.

This module provides a hybrid token extractor used by SSE endpoints:
- Authorization: Bearer <token>
- ?token=<token> for specific SSE paths
"""

from fastapi import HTTPException, Request


def extract_token_from_header_or_query(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token

    token = request.query_params.get("token")
    if token:
        return token

    raise HTTPException(status_code=401, detail="Missing authentication token")

