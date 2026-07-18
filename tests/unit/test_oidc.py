"""Controlled in-process OIDC provider fixtures."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from pentagon5_auth.config import AuthSettings
from pentagon5_auth.oidc import OIDCClient, OIDCError
from pentagon5_runtime.config import RuntimeSettings

ISSUER = "http://oidc.test"
CLIENT_ID = "pentagon5-test"
NONCE = "fixture-nonce"


def settings() -> AuthSettings:
    return AuthSettings(
        runtime=RuntimeSettings("auth-test", "test", "postgresql://db/test"),
        issuer=ISSUER,
        client_id=CLIENT_ID,
        client_secret="fixture-secret",  # pragma: allowlist secret
        redirect_uri="http://gateway.test/v1/auth/oidc/callback",
        hmac_key=b"h" * 32,
    )


def provider_transport(*, nonce: str = NONCE) -> httpx.MockTransport:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(private_key.public_key()))
    public_jwk["kid"] = "fixture-key"
    now = datetime.now(UTC)
    id_token = jwt.encode(
        {
            "iss": ISSUER,
            "aud": CLIENT_ID,
            "sub": "fixture-subject",
            "nonce": nonce,
            "email": "user@example.test",
            "email_verified": True,
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "fixture-key"},
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/.well-known/openid-configuration":
            return httpx.Response(
                200,
                json={
                    "issuer": ISSUER,
                    "authorization_endpoint": f"{ISSUER}/authorize",
                    "token_endpoint": f"{ISSUER}/token",
                    "jwks_uri": f"{ISSUER}/jwks",
                },
            )
        if request.url.path == "/token":
            form = parse_qs(request.content.decode())
            assert form["code_verifier"] == ["fixture-verifier"]
            assert form["grant_type"] == ["authorization_code"]
            return httpx.Response(200, json={"id_token": id_token})
        if request.url.path == "/jwks":
            return httpx.Response(200, json={"keys": [public_jwk]})
        raise AssertionError(f"unexpected provider request: {request.url}")

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_authorization_url_uses_code_pkce_and_oidc_nonce() -> None:
    async with httpx.AsyncClient(transport=provider_transport()) as client:
        oidc = OIDCClient(settings(), client)
        url = await oidc.authorization_url(
            state="fixture-state",
            nonce=NONCE,
            code_challenge="fixture-challenge",
        )
    query = parse_qs(urlparse(url).query)
    assert query["response_type"] == ["code"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["code_challenge"] == ["fixture-challenge"]
    assert query["nonce"] == [NONCE]


@pytest.mark.asyncio
async def test_token_exchange_validates_signed_id_token() -> None:
    async with httpx.AsyncClient(transport=provider_transport()) as client:
        claims = await OIDCClient(settings(), client).exchange(
            code="fixture-code",
            verifier="fixture-verifier",
            nonce=NONCE,
        )
    assert claims["sub"] == "fixture-subject"
    assert claims["email_verified"] is True


@pytest.mark.asyncio
async def test_token_exchange_rejects_nonce_mismatch() -> None:
    async with httpx.AsyncClient(transport=provider_transport(nonce="wrong")) as client:
        with pytest.raises(OIDCError, match="nonce"):
            await OIDCClient(settings(), client).exchange(
                code="fixture-code",
                verifier="fixture-verifier",
                nonce=NONCE,
            )
