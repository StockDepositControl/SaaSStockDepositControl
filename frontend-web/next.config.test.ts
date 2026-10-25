import { describe, expect, it } from "vitest";
import nextConfig from "./next.config";

describe("next.config", () => {
  it("emits a standalone server bundle", () => {
    expect(nextConfig.output).toBe("standalone");
  });

  it("does not hardcode a backend rewrite (single-origin proxy routes /api)", () => {
    expect(nextConfig.rewrites).toBeUndefined();
  });

  it("does not hardcode LAN IPs in allowedDevOrigins", () => {
    const lanOrigins = (nextConfig.allowedDevOrigins ?? []).filter((o) => o.startsWith("192.168."));
    expect(lanOrigins).toEqual([]);
  });
});
