"""Provider-neutral OpenID Connect Authorization Code client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

from pentagon5_auth.config import AuthSettings


class OIDCError(ValueError):
    """Raised when provider metadata or token validation fails."""


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str


class OIDCClient:
    """OIDC discovery, authorization, token exchange, and ID-token validation."""

    def __init__(self, settings: AuthSettings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client
        self._metadata: ProviderMetadata | None = None

    async def metadata(self) -> ProviderMetadata:
        if self._metadata is not None:
            return self._metadata
        response = await self._client.get(
            f"{self._settings.issuer}/.well-known/openid-configuration"
        )
        response.raise_for_status()
        document = response.json()
        if document.get("issuer") != self._settings.issuer:
            raise OIDCError("discovered issuer does not match configured issuer")
        try:
            metadata = ProviderMetadata(
                authorization_endpoint=str(document["authorization_endpoint"]),
                token_endpoint=str(document["token_endpoint"]),
                jwks_uri=str(document["jwks_uri"]),
            )
        except KeyError as error:
            raise OIDCError("provider metadata is incomplete") from error
        endpoints = (
            metadata.authorization_endpoint,
            metadata.token_endpoint,
            metadata.jwks_uri,
        )
        if not all(value.startswith(("https://", "http://")) for value in endpoints):
            raise OIDCError("provider endpoints must be absolute HTTP URLs")
        if self._settings.runtime.environment not in {"development", "test"} and not all(
            value.startswith("https://") for value in endpoints
        ):
            raise OIDCError("provider endpoints must use HTTPS")
        self._metadata = metadata
        return metadata

    async def authorization_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
    ) -> str:
        metadata = await self.metadata()
        query = urlencode(
            {
                "client_id": self._settings.client_id,
                "redirect_uri": self._settings.redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
        )
        return f"{metadata.authorization_endpoint}?{query}"

    async def exchange(self, *, code: str, verifier: str, nonce: str) -> dict[str, Any]:
        metadata = await self.metadata()
        response = await self._client.post(
            metadata.token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self._settings.redirect_uri,
                "client_id": self._settings.client_id,
                "client_secret": self._settings.client_secret,
                "code_verifier": verifier,
            },
        )
        response.raise_for_status()
        id_token = response.json().get("id_token")
        if not isinstance(id_token, str):
            raise OIDCError("token response did not contain an ID token")
        jwks_response = await self._client.get(metadata.jwks_uri)
        jwks_response.raise_for_status()
        header = jwt.get_unverified_header(id_token)
        algorithm = header.get("alg")
        if algorithm not in {"RS256", "ES256"}:
            raise OIDCError("ID token uses an unsupported algorithm")
        kid = header.get("kid")
        keys = jwks_response.json().get("keys", [])
        matching = [key for key in keys if key.get("kid") == kid]
        if len(matching) != 1:
            raise OIDCError("ID token signing key was not uniquely identified")
        claims: dict[str, Any] = jwt.decode(
            id_token,
            jwt.PyJWK.from_dict(matching[0]).key,
            algorithms=[algorithm],
            audience=self._settings.client_id,
            issuer=self._settings.issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub", "nonce"]},
        )
        if claims.get("nonce") != nonce:
            raise OIDCError("ID token nonce does not match")
        if claims.get("email_verified") is not True:
            raise OIDCError("provider email is not verified")
        return claims
