import { describe, expect, it } from "vitest";
import { parseAuthCallback } from "./platform";

describe("parseAuthCallback", () => {
  it("accepts the fixed desktop callback shape", () => {
    const code = "g".repeat(32);
    expect(
      parseAuthCallback(`pentagon5://auth/callback?code=${code}`),
    ).toEqual({ code });
  });

  it("returns a provider denial code", () => {
    expect(
      parseAuthCallback("pentagon5://auth/callback?error=access_denied"),
    ).toEqual({
      error: "access_denied",
    });
  });

  it.each([
    `https://example.test/callback?code=${"g".repeat(32)}`,
    `pentagon5://other/callback?code=${"g".repeat(32)}`,
    "pentagon5://auth/callback?code=short",
    `pentagon5://auth/callback?code=${"g".repeat(32)}&state=unexpected`,
    "pentagon5://auth/callback?error=denied&error_description=extra",
    "pentagon5://auth/callback",
  ])("rejects unexpected callback %s", (value) => {
    expect(() => parseAuthCallback(value)).toThrow();
  });
});
