"""Small, auditable security primitives shared by backend services."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


def random_token(bytes_count: int = 32) -> str:
    """Return a URL-safe, high-entropy opaque token."""
    if bytes_count < 32:
        raise ValueError("security tokens require at least 256 bits")
    return secrets.token_urlsafe(bytes_count)


def fingerprint(token: str, key: bytes) -> str:
    """Create a keyed, non-reversible lookup value for an opaque token."""
    if len(key) < 32:
        raise ValueError("fingerprint keys require at least 256 bits")
    return hmac.new(key, token.encode(), hashlib.sha256).hexdigest()


def pkce_challenge(verifier: str) -> str:
    """Create an RFC 7636 S256 PKCE challenge."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def constant_time_equal(left: str, right: str) -> bool:
    """Compare secrets without data-dependent early exit."""
    return hmac.compare_digest(left, right)
