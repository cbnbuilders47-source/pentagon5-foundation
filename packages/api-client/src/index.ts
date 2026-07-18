import { z } from "zod";

const uuidV7Pattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const uppercaseCodePattern = /^[A-Z][A-Z0-9_]*$/;
const uuidV7 = z.string().regex(uuidV7Pattern);
const utcTimestamp = z
  .string()
  .datetime({ offset: false })
  .refine((value) => value.endsWith("Z"), "Expected a UTC Z timestamp");
const httpUrl = z.string().url().refine((value) => {
  const protocol = new URL(value).protocol;
  return protocol === "http:" || protocol === "https:";
}, "Expected an HTTP(S) URL");

const metadataSchema = z.strictObject({
  correlationId: uuidV7,
  causationId: uuidV7.optional(),
});
const baseEnvelopeShape = {
  schemaVersion: z.literal("1.0.0"),
  messageId: uuidV7,
  occurredAt: utcTimestamp,
  metadata: metadataSchema,
};
const backendStatusSchema = z.strictObject({
  schemaVersion: z.literal("1.0.0"),
  id: uuidV7,
  component: z.string().min(1),
  status: z.enum(["healthy", "degraded", "unavailable"]),
  observedAt: utcTimestamp,
  detail: z.string().min(1).optional(),
});
const healthEnvelopeSchema = z.strictObject({
  ...baseEnvelopeShape,
  category: z.literal("health"),
  payload: backendStatusSchema,
});
const errorPayloadSchema = z.strictObject({
  code: z.string().regex(uppercaseCodePattern),
  message: z.string().min(1),
  retryable: z.boolean(),
  field: z.string().min(1).optional(),
});
const errorEnvelopeSchema = z.strictObject({
  ...baseEnvelopeShape,
  category: z.literal("error"),
  payload: errorPayloadSchema,
});
const loginLaunchSchema = z.strictObject({
  authorization_url: httpUrl,
});
const uniqueStrings = (maximum: number) =>
  z
    .array(z.string().min(1).max(maximum))
    .refine((values) => new Set(values).size === values.length, "Expected unique values");
const sessionSchema = z.strictObject({
  user_id: uuidV7,
  session_id: uuidV7,
  email: z.string().email().max(320),
  display_name: z.string().min(1).max(120),
  roles: uniqueStrings(80),
  permissions: uniqueStrings(120),
  expires_at: utcTimestamp,
});
const loginGrantSchema = z.strictObject({
  session_token: z.string().min(32),
  session: sessionSchema,
});
const channelSchema = z.enum(["system.health", "session.events"]);
const wsTicketResponseSchema = z.strictObject({
  ticket: z.string().min(32),
  channel: channelSchema,
  expires_in_seconds: z.number().int().min(1).max(60),
});
const websocketPayloadSchema = z.strictObject({
  operation: z.enum(["subscribe", "unsubscribe", "ack", "heartbeat"]),
  channel: channelSchema,
  subscriptionId: uuidV7.optional(),
});
const websocketEnvelopeSchema = z.strictObject({
  ...baseEnvelopeShape,
  category: z.literal("websocket"),
  payload: websocketPayloadSchema,
});
const incomingEnvelopeSchema = z.discriminatedUnion("category", [
  healthEnvelopeSchema,
  websocketEnvelopeSchema,
]);

export type BackendStatus = z.infer<typeof backendStatusSchema>;
export type LoginLaunch = z.infer<typeof loginLaunchSchema>;
export type Session = z.infer<typeof sessionSchema>;
export type AuthSession = z.infer<typeof loginGrantSchema>;
export type WsChannel = z.infer<typeof channelSchema>;
export type ApiErrorPayload = z.infer<typeof errorPayloadSchema>;
export type IncomingEnvelope = z.infer<typeof incomingEnvelopeSchema>;

export interface AuthCallback {
  code?: string;
  error?: string;
}

export interface WsTicket {
  ticket: string;
  channel: WsChannel;
  expires_in_seconds: number;
  websocket_url: string;
}

export interface ApiClientOptions {
  baseUrl: string;
  fetch?: typeof globalThis.fetch;
}

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly retryable: boolean;
  readonly field: string | undefined;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = payload.code;
    this.retryable = payload.retryable;
    this.field = payload.field;
  }
}

function normalizeBaseUrl(value: string): string {
  const parsed = new URL(httpUrl.parse(value));
  parsed.pathname = parsed.pathname.replace(/\/+$/, "");
  parsed.search = "";
  parsed.hash = "";
  return parsed.toString().replace(/\/$/, "");
}

function parseError(body: unknown, status: number): ApiClientError {
  const parsed = errorEnvelopeSchema.safeParse(body);
  return new ApiClientError(
    status,
    parsed.success
      ? parsed.data.payload
      : {
          code: "INVALID_ERROR_ENVELOPE",
          message: `Backend returned an invalid error envelope (${status})`,
          retryable: false,
        },
  );
}

function websocketUrl(baseUrl: string, channel: WsChannel): string {
  const url = new URL(baseUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = `${url.pathname.replace(/\/$/, "")}/v1/ws/${channel}`;
  return url.toString();
}

export class PentagonApiClient {
  readonly system: {
    getStatus: () => Promise<BackendStatus>;
  };
  readonly auth: {
    beginOidcLogin: (deviceKey: string) => Promise<LoginLaunch>;
    exchangeOidcGrant: (code: string) => Promise<AuthSession>;
    getSession: (token: string) => Promise<Session>;
    logout: (token: string) => Promise<void>;
  };
  readonly ws: {
    createTicket: (token: string, channel?: WsChannel) => Promise<WsTicket>;
  };

  private readonly baseUrl: string;
  private readonly fetchImpl: typeof globalThis.fetch;

  constructor(options: ApiClientOptions) {
    this.baseUrl = normalizeBaseUrl(options.baseUrl);
    this.fetchImpl = options.fetch ?? globalThis.fetch.bind(globalThis);
    this.system = {
      getStatus: async () => {
        const envelope = await this.request(
          "/v1/system/health/ready",
          healthEnvelopeSchema,
        );
        return envelope.payload;
      },
    };
    this.auth = {
      beginOidcLogin: (deviceKey) => {
        if (deviceKey.length < 8 || deviceKey.length > 200) {
          throw new TypeError("Device key must contain 8 to 200 characters");
        }
        return this.request("/v1/auth/oidc/start", loginLaunchSchema, {
          method: "POST",
          body: JSON.stringify({ device_key: deviceKey, platform: "macos" }),
        });
      },
      exchangeOidcGrant: (code) => {
        if (code.length < 32 || code.length > 512) {
          throw new TypeError("Login grant must contain 32 to 512 characters");
        }
        return this.request("/v1/auth/oidc/exchange", loginGrantSchema, {
          method: "POST",
          body: JSON.stringify({ code }),
        });
      },
      getSession: (token) =>
        this.request("/v1/auth/session", sessionSchema, {
          headers: this.authHeaders(token),
        }),
      logout: (token) =>
        this.requestVoid("/v1/auth/logout", {
          method: "POST",
          headers: this.authHeaders(token),
        }),
    };
    this.ws = {
      createTicket: async (token, channel = "system.health") => {
        const response = await this.request(
          "/v1/auth/ws-tickets",
          wsTicketResponseSchema,
          {
            method: "POST",
            headers: this.authHeaders(token),
            body: JSON.stringify({ channel }),
          },
        );
        return {
          ...response,
          websocket_url: websocketUrl(this.baseUrl, response.channel),
        };
      },
    };
  }

  private authHeaders(token: string): HeadersInit {
    if (!token.trim()) {
      throw new TypeError("Authentication token must not be empty");
    }
    return { Authorization: `Bearer ${token}` };
  }

  private async request<T>(
    path: string,
    schema: z.ZodType<T>,
    init: RequestInit = {},
  ): Promise<T> {
    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...init.headers,
      },
    });
    const body: unknown = await response.json().catch(() => undefined);
    if (!response.ok) throw parseError(body, response.status);
    return schema.parse(body);
  }

  private async requestVoid(path: string, init: RequestInit): Promise<void> {
    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...init.headers },
    });
    if (!response.ok) {
      const body: unknown = await response.json().catch(() => undefined);
      throw parseError(body, response.status);
    }
  }
}

export function createUuidV7(now = Date.now(), random = crypto.getRandomValues(new Uint8Array(10))): string {
  if (random.length !== 10) throw new TypeError("UUIDv7 requires 10 random bytes");
  const bytes = new Uint8Array(16);
  let timestamp = BigInt(now);
  for (let index = 5; index >= 0; index -= 1) {
    bytes[index] = Number(timestamp & 0xffn);
    timestamp >>= 8n;
  }
  bytes.set(random, 6);
  bytes[6] = 0x70 | (bytes[6]! & 0x0f);
  bytes[8] = 0x80 | (bytes[8]! & 0x3f);
  const hex = [...bytes].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function createWebSocketSubscribeEnvelope(
  channel: WsChannel,
  now = new Date(),
): z.infer<typeof websocketEnvelopeSchema> {
  const correlationId = createUuidV7(now.getTime());
  return {
    schemaVersion: "1.0.0",
    messageId: createUuidV7(now.getTime()),
    category: "websocket",
    occurredAt: now.toISOString(),
    metadata: { correlationId },
    payload: {
      operation: "subscribe",
      channel,
      subscriptionId: createUuidV7(now.getTime()),
    },
  };
}

export function parseIncomingEnvelope(value: unknown): IncomingEnvelope {
  return incomingEnvelopeSchema.parse(value);
}

export type WebSocketFactory = (url: string) => WebSocket;
export type WebSocketState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "denied";

export interface ReconnectingSocketOptions {
  getTicket: () => Promise<WsTicket>;
  onStateChange: (state: WebSocketState) => void;
  onEnvelope?: (envelope: IncomingEnvelope) => void;
  webSocketFactory?: WebSocketFactory;
  maxAttempts?: number;
  baseDelayMs?: number;
}

export class ReconnectingWebSocket {
  private socket: WebSocket | undefined;
  private stopped = true;
  private attempts = 0;
  private timer: ReturnType<typeof setTimeout> | undefined;

  constructor(private readonly options: ReconnectingSocketOptions) {}

  start(): void {
    if (!this.stopped) return;
    this.stopped = false;
    this.attempts = 0;
    void this.connect("connecting");
  }

  stop(): void {
    this.stopped = true;
    if (this.timer) clearTimeout(this.timer);
    this.socket?.close(1000, "client logout");
    this.options.onStateChange("disconnected");
  }

  private async connect(state: "connecting" | "reconnecting"): Promise<void> {
    this.options.onStateChange(state);
    try {
      const ticket = await this.options.getTicket();
      if (this.stopped) return;
      const url = new URL(ticket.websocket_url);
      url.searchParams.set("ticket", ticket.ticket);
      const factory = this.options.webSocketFactory ?? ((value) => new WebSocket(value));
      this.socket = factory(url.toString());
      this.socket.onopen = () => {
        this.attempts = 0;
        this.socket?.send(
          JSON.stringify(createWebSocketSubscribeEnvelope(ticket.channel)),
        );
        this.options.onStateChange("connected");
      };
      this.socket.onmessage = (event) => {
        try {
          const raw: unknown =
            typeof event.data === "string" ? JSON.parse(event.data) : undefined;
          this.options.onEnvelope?.(parseIncomingEnvelope(raw));
        } catch {
          this.options.onStateChange("denied");
          this.socket?.close(1008, "invalid server envelope");
        }
      };
      this.socket.onclose = (event) => {
        this.socket = undefined;
        if (this.stopped) return;
        if (event.code === 1008 || event.code === 4401 || event.code === 4403) {
          this.options.onStateChange("denied");
          return;
        }
        this.scheduleReconnect();
      };
      this.socket.onerror = () => this.socket?.close();
    } catch (error) {
      if (this.stopped) return;
      if (error instanceof ApiClientError && (error.status === 401 || error.status === 403)) {
        this.options.onStateChange("denied");
        return;
      }
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    const maxAttempts = this.options.maxAttempts ?? 5;
    if (this.attempts >= maxAttempts) {
      this.options.onStateChange("disconnected");
      return;
    }
    const delay = Math.min(
      (this.options.baseDelayMs ?? 500) * 2 ** this.attempts,
      15_000,
    );
    this.attempts += 1;
    this.options.onStateChange("reconnecting");
    this.timer = setTimeout(() => void this.connect("reconnecting"), delay);
  }
}
