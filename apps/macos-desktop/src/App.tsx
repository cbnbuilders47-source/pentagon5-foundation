import {
  ApiClientError,
  PentagonApiClient,
  ReconnectingWebSocket,
  type BackendStatus,
  type Session,
  type WebSocketState,
} from "@pentagon5/api-client";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  desktopPlatform,
  parseAuthCallback,
  type DesktopPlatform,
} from "./platform";

const DEFAULT_BACKEND = "http://127.0.0.1:8000";

type SessionState =
  | "disconnected"
  | "signed-out"
  | "authenticating"
  | "authenticated"
  | "expired"
  | "denied";

interface AppProps {
  backendUrl?: string;
  platform?: DesktopPlatform;
  client?: PentagonApiClient;
}

export function App({
  backendUrl = import.meta.env.VITE_BACKEND_URL ?? DEFAULT_BACKEND,
  platform = desktopPlatform,
  client: suppliedClient,
}: AppProps) {
  const client = useMemo(
    () => suppliedClient ?? new PentagonApiClient({ baseUrl: backendUrl }),
    [backendUrl, suppliedClient],
  );
  const [backend, setBackend] = useState<BackendStatus>();
  const [session, setSession] = useState<SessionState>("disconnected");
  const [user, setUser] = useState<Session>();
  const [token, setToken] = useState<string>();
  const [socketState, setSocketState] = useState<WebSocketState>("disconnected");
  const [message, setMessage] = useState("Checking backend…");
  const socket = useRef<ReconnectingWebSocket | undefined>(undefined);

  const stopSocket = useCallback(() => {
    socket.current?.stop();
    socket.current = undefined;
  }, []);

  const authenticate = useCallback(
    async (opaqueToken: string) => {
      try {
        const currentUser = await client.auth.getSession(opaqueToken);
        setToken(opaqueToken);
        setUser(currentUser);
        setSession("authenticated");
        setMessage("Signed in");
      } catch (error) {
        await platform.deleteToken().catch(() => undefined);
        setToken(undefined);
        setUser(undefined);
        setSession(error instanceof ApiClientError && error.status === 403 ? "denied" : "expired");
        setMessage(error instanceof Error ? error.message : "Session expired");
      }
    },
    [client, platform],
  );

  useEffect(() => {
    let active = true;
    void Promise.all([client.system.getStatus(), platform.loadToken()])
      .then(([status, savedToken]) => {
        if (!active) return;
        setBackend(status);
        if (savedToken) {
          void authenticate(savedToken);
        } else {
          setSession("signed-out");
          setMessage("Sign in to continue");
        }
      })
      .catch((error: unknown) => {
        if (!active) return;
        setSession("disconnected");
        setMessage(error instanceof Error ? error.message : "Backend unavailable");
      });
    return () => {
      active = false;
    };
  }, [authenticate, client, platform]);

  const handleCallback = useCallback(
    async (callbackUrl: string) => {
      setSession("authenticating");
      try {
        const callback = parseAuthCallback(callbackUrl);
        if (callback.error) {
          setSession("denied");
          setMessage(callback.error);
          return;
        }
        if (!callback.code) throw new Error("Authentication callback has no grant code");
        const result = await client.auth.exchangeOidcGrant(callback.code);
        await platform.storeToken(result.session_token);
        setToken(result.session_token);
        setUser(result.session);
        setSession("authenticated");
        setMessage("Signed in");
      } catch (error) {
        setSession("denied");
        setMessage(error instanceof Error ? error.message : "Login denied");
      }
    },
    [client, platform],
  );

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    void platform.authCallbacks((url) => void handleCallback(url)).then((cleanup) => {
      unlisten = cleanup;
    });
    return () => unlisten?.();
  }, [handleCallback, platform]);

  useEffect(() => {
    if (session !== "authenticated" || !token) {
      stopSocket();
      return;
    }
    const connection = new ReconnectingWebSocket({
      getTicket: () => client.ws.createTicket(token),
      onStateChange: setSocketState,
    });
    socket.current = connection;
    connection.start();
    return () => connection.stop();
  }, [client, session, stopSocket, token]);

  const login = async () => {
    setSession("authenticating");
    setMessage("Opening your system browser…");
    try {
      const deviceKey = await platform.getOrCreateDeviceKey();
      const launch = await client.auth.beginOidcLogin(deviceKey);
      await platform.openOidcLogin(launch.authorization_url);
    } catch (error) {
      setSession("disconnected");
      setMessage(error instanceof Error ? error.message : "Unable to start login");
    }
  };

  const logout = async () => {
    stopSocket();
    if (token) await client.auth.logout(token).catch(() => undefined);
    await platform.deleteToken();
    setToken(undefined);
    setUser(undefined);
    setSession("signed-out");
    setMessage("Signed out");
  };

  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">Pentagon 5</p>
          <h1>Desktop</h1>
        </div>
        <span className={`badge ${backend?.status ?? "unavailable"}`}>
          {backend?.status ?? "offline"}
        </span>
      </header>

      <section className="card endpoint">
        <span>Backend</span>
        <code>{backendUrl}</code>
      </section>

      <section className="card session">
        <div>
          <p className="eyebrow">Session</p>
          <h2>{user?.display_name ?? user?.email ?? user?.user_id ?? session}</h2>
          <p role="status">{message}</p>
        </div>
        {session === "authenticated" ? (
          <button className="secondary" onClick={() => void logout()}>Log out</button>
        ) : (
          <button
            onClick={() => void login()}
            disabled={session === "authenticating" || !backend}
          >
            {session === "authenticating" ? "Waiting for browser…" : "Sign in"}
          </button>
        )}
      </section>

      <section className="card connection">
        <div>
          <p className="eyebrow">Live connection</p>
          <h2>{socketState}</h2>
        </div>
        <span className={`dot ${socketState}`} aria-label={`WebSocket ${socketState}`} />
      </section>
    </main>
  );
}
