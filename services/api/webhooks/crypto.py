import hashlib
import hmac
import time


def sign(body: bytes, secret: str, timestamp: int | None = None) -> dict[str, str]:
    ts = int(time.time()) if timestamp is None else timestamp
    message = f"{ts}.".encode() + body
    digest = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return {"X-Pulse-Timestamp": str(ts), "X-Pulse-Signature": f"sha256={digest}"}
