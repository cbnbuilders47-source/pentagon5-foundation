import { describe, expect, it, vi } from "vitest";
import {
  ApiClientError,
  PentagonApiClient,
  ReconnectingWebSocket,
  createUuidV7,
  createWebSocketSubscribeEnvelope,
  parseIncomingEnvelope,
} from "../src";

const MESSAGE_ID = "018f22e2-7d00-7000-8000-000000000001";
const CORRELATION_ID = "018f22e2-7d00-7000-8000-000000000002";
const USER_ID = "018f22e2-7d00-7000-8000-000000000003";
const SESSION_ID = "018f22e2-7d00-7000-8000-000000000004";
const uuidV7PatternForTest =
  /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function healthEnvelope() {
  return {
    schemaVersion: "1.0.0",
    messageId: MESSAGE_ID,
    category: "health",
    occurredAt: "2026-07-18T12:00:00Z",
    metadata: { correlationId: CORRELATION_ID },
    payload: {
      schemaVersion: "1.0.0",
      id: USER_ID,
      component: "authentication",
      status: "healthy",
      observedAt: "2026-07-18T12:00:00Z",
      detail: "database connection available",
    },
  };
}

function session() {
  return {
    user_id: USER_ID,
    session_id: SESSION_ID,
    email: "user@example.test",
    display_name: "Example User",
    roles: ["user"],
    permissions: ["system.health.read"],
    expires_at: "2026-07-18T13:00:00Z",
  };
}

describe("PentagonApiClient", () => {
  it("parses the exact readiness health envelope", async () => {
    const fetch = vi.fn(async () => jsonResponse(healthEnvelope()));
    const client = new PentagonApiClient({ baseUrl: "https://api.example.test/", fetch });

    await expect(client.system.getStatus()).resolves.toEqual(healthEnvelope().payload);
    expect(fetch).toHaveBeenCalledWith(
      "https://api.example.test/v1/system/health/ready",
      expect.any(Object),
    );
  });

  it("sends the exact macOS login start body and validates the raw response", async () => {
    const fetch = vi.fn(
      async (_input: RequestInfo | URL, _init?: RequestInit) =>
        jsonResponse({ authorization_url: "https://id.example.test/authorize" }),
    );
    const client = new PentagonApiClient({ baseUrl: "https://api.example.test", fetch });

    await client.auth.beginOidcLogin("stable-device-key");
    expect(fetch.mock.calls[0]?.[0]).toBe("https://api.example.test/v1/auth/oidc/start");
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toEqual({
      device_key: "stable-device-key",
      platform: "macos",
    });
  });

  it("exchanges a one-time grant and validates the snake-case session", async () => {
    const code = "g".repeat(32);
    const fetch = vi.fn(
      async (_input: RequestInfo | URL, _init?: RequestInit) =>
        jsonResponse({ session_token: "t".repeat(32), session: session() }),
    );
    const client = new PentagonApiClient({ baseUrl: "https://api.example.test", fetch });

    await expect(client.auth.exchangeOidcGrant(code)).resolves.toEqual({
      session_token: "t".repeat(32),
      session: session(),
    });
    expect(fetch.mock.calls[0]?.[0]).toBe("https://api.example.test/v1/auth/oidc/exchange");
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toEqual({ code });
  });

  it("uses bearer auth for session, logout, and the exact ticket body", async () => {
    const fetch = vi.fn(
      async (input: RequestInfo | URL, _init?: RequestInit) =>
        String(input).endsWith("ws-tickets")
          ? jsonResponse({
              ticket: "w".repeat(32),
              channel: "system.health",
              expires_in_seconds: 30,
            })
          : String(input).endsWith("logout")
            ? new Response(null, { status: 204 })
            : jsonResponse(session()),
    );
    const client = new PentagonApiClient({
      baseUrl: "http://127.0.0.1:8000",
      fetch,
    });

    await client.auth.getSession("opaque-token");
    await client.auth.logout("opaque-token");
    await expect(client.ws.createTicket("opaque-token")).resolves.toMatchObject({
      channel: "system.health",
      websocket_url: "ws://127.0.0.1:8000/v1/ws/system.health",
    });
    for (const call of fetch.mock.calls) {
      expect(call[1]?.headers).toMatchObject({ Authorization: "Bearer opaque-token" });
    }
    expect(fetch.mock.calls.map((call) => call[0])).toEqual([
      "http://127.0.0.1:8000/v1/auth/session",
      "http://127.0.0.1:8000/v1/auth/logout",
      "http://127.0.0.1:8000/v1/auth/ws-tickets",
    ]);
    expect(JSON.parse(String(fetch.mock.calls[2]?.[1]?.body))).toEqual({
      channel: "system.health",
    });
  });

  it("parses only the accepted uppercase Error envelope", async () => {
    const fetch = vi.fn(async () =>
      jsonResponse(
        {
          schemaVersion: "1.0.0",
          messageId: MESSAGE_ID,
          category: "error",
          occurredAt: "2026-07-18T12:00:00Z",
          metadata: { correlationId: CORRELATION_ID },
          payload: {
            code: "SESSION_INVALID",
            message: "Session is invalid or expired",
            retryable: false,
          },
        },
        401,
      ),
    );
    const client = new PentagonApiClient({ baseUrl: "https://api.example.test", fetch });

    await expect(client.auth.getSession("opaque-token")).rejects.toMatchObject({
      status: 401,
      code: "SESSION_INVALID",
      retryable: false,
    } satisfies Partial<ApiClientError>);
  });

  it("does not accept lowercase legacy error codes", async () => {
    const malformed = {
      ...healthEnvelope(),
      category: "error",
      payload: { code: "session_invalid", message: "Invalid", retryable: false },
    };
    const client = new PentagonApiClient({
      baseUrl: "https://api.example.test",
      fetch: async () => jsonResponse(malformed, 401),
    });
    await expect(client.auth.getSession("opaque-token")).rejects.toMatchObject({
      code: "INVALID_ERROR_ENVELOPE",
    });
  });

  it("rejects legacy and malformed response fallbacks", async () => {
    const client = new PentagonApiClient({
      baseUrl: "https://api.example.test",
      fetch: async () => jsonResponse({ data: healthEnvelope().payload }),
    });
    await expect(client.system.getStatus()).rejects.toThrow();
  });
});

describe("accepted WebSocket envelopes", () => {
  it("generates lowercase UUIDv7 values and a valid subscribe envelope", () => {
    const id = createUuidV7(1_721_304_000_000, new Uint8Array(10));
    expect(id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-8[0-9a-f]{3}-[0-9a-f]{12}$/);

    const envelope = createWebSocketSubscribeEnvelope(
      "system.health",
      new Date("2026-07-18T12:00:00Z"),
    );
    expect(envelope.category).toBe("websocket");
    expect(envelope.occurredAt).toBe("2026-07-18T12:00:00.000Z");
    expect(envelope.payload).toMatchObject({
      operation: "subscribe",
      channel: "system.health",
    });
    for (const value of [
      envelope.messageId,
      envelope.metadata.correlationId,
      envelope.payload.subscriptionId,
    ]) {
      expect(value).toMatch(uuidV7PatternForTest);
    }
  });

  it("validates accepted incoming metadata and rejects arbitrary messages", () => {
    expect(parseIncomingEnvelope(healthEnvelope()).category).toBe("health");
    expect(() => parseIncomingEnvelope({ category: "health", payload: {} })).toThrow();
  });

  it("sends subscribe on open and does not pass invalid messages", async () => {
    const states: string[] = [];
    const envelopes: unknown[] = [];
    const send = vi.fn();
    const fakeSocket = {
      send,
      close: vi.fn(),
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
    } as unknown as WebSocket;
    const connection = new ReconnectingWebSocket({
      getTicket: async () => ({
        ticket: "w".repeat(32),
        channel: "system.health",
        expires_in_seconds: 30,
        websocket_url: "wss://api.example.test/v1/ws/system.health",
      }),
      onStateChange: (state) => states.push(state),
      onEnvelope: (envelope) => envelopes.push(envelope),
      webSocketFactory: () => fakeSocket,
    });

    connection.start();
    await vi.waitFor(() => expect(fakeSocket.onopen).toBeTypeOf("function"));
    fakeSocket.onopen?.(new Event("open"));
    expect(JSON.parse(String(send.mock.calls[0]?.[0]))).toMatchObject({
      category: "websocket",
      payload: { operation: "subscribe", channel: "system.health" },
    });
    fakeSocket.onmessage?.(
      new MessageEvent("message", { data: JSON.stringify({ arbitrary: true }) }),
    );
    expect(envelopes).toEqual([]);
    expect(fakeSocket.close).toHaveBeenCalledWith(1008, "invalid server envelope");
    expect(states).toContain("denied");
  });
});
