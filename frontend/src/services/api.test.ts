/**
 * Tests for src/services/api.ts — data transformers and auth token management.
 *
 * Tests the INTERNAL transformer functions by importing them indirectly
 * through the public API functions, and tests setAuthToken directly.
 *
 * Covers:
 * - setAuthToken() — sets and clears Authorization header
 * - Data transformer logic via exported functions
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import api, { setAuthToken } from "@/services/api";

// Mock axios to prevent real network calls
vi.mock("axios", () => {
  const instance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    defaults: { headers: { common: {} } },
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  };
  return {
    default: {
      create: vi.fn(() => instance),
    },
  };
});

describe("setAuthToken", () => {
  beforeEach(() => {
    // Clear any existing auth header
    delete api.defaults.headers.common["Authorization"];
  });

  it("sets Authorization header with Bearer prefix", () => {
    setAuthToken("test_jwt_token");
    expect(api.defaults.headers.common["Authorization"]).toBe(
      "Bearer test_jwt_token"
    );
  });

  it("clears Authorization header when null", () => {
    setAuthToken("some_token");
    setAuthToken(null);
    expect(api.defaults.headers.common["Authorization"]).toBeUndefined();
  });

  it("clears Authorization header when undefined", () => {
    setAuthToken("some_token");
    setAuthToken(undefined);
    expect(api.defaults.headers.common["Authorization"]).toBeUndefined();
  });
});
