"""Спільний пул httpx.AsyncClient на весь процес.

Один клієнт = один пул з'єднань. Новий клієнт на кожен запит — це витік
з'єднань і зрештою httpx.PoolTimeout під навантаженням.
"""

import httpx

DEFAULT_TIMEOUT = httpx.Timeout(10.0)
_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _client


async def close_http_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
