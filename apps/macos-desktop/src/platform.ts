import { invoke } from "@tauri-apps/api/core";
import { getCurrent, onOpenUrl } from "@tauri-apps/plugin-deep-link";

export const CALLBACK_SCHEME = "pentagon5:";

export interface ParsedAuthCallback {
  code?: string;
  error?: string;
}

export function parseAuthCallback(value: string): ParsedAuthCallback {
  const url = new URL(value);
  if (
    url.protocol !== CALLBACK_SCHEME ||
    url.hostname !== "auth" ||
    url.pathname !== "/callback"
  ) {
    throw new Error("Unexpected authentication callback URL");
  }
  if (url.username || url.password || url.port || url.hash) {
    throw new Error("Authentication callback contains forbidden URL components");
  }
  const entries = [...url.searchParams.entries()];
  if (entries.length !== 1) {
    throw new Error("Authentication callback must contain exactly one result");
  }
  const code = url.searchParams.get("code") ?? undefined;
  const error = url.searchParams.get("error") ?? undefined;
  if ((code && error) || (!code && !error)) {
    throw new Error("Authentication callback has no valid result");
  }
  if (code && (code.length < 32 || code.length > 512)) {
    throw new Error("Authentication grant code has an invalid length");
  }
  return {
    ...(code ? { code } : {}),
    ...(error ? { error } : {}),
  };
}

export const desktopPlatform = {
  loadToken: () => invoke<string | null>("load_auth_token"),
  storeToken: (token: string) => invoke<void>("store_auth_token", { token }),
  deleteToken: () => invoke<void>("delete_auth_token"),
  getOrCreateDeviceKey: () => invoke<string>("get_or_create_device_key"),
  openOidcLogin: (authorizationUrl: string) =>
    invoke<void>("open_oidc_login", { authorizationUrl }),
  authCallbacks: async (handler: (url: string) => void) => {
    const current = await getCurrent();
    current?.forEach(handler);
    return onOpenUrl((urls) => urls.forEach(handler));
  },
};

export type DesktopPlatform = typeof desktopPlatform;
