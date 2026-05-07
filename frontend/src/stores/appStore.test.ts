/**
 * Tests for src/stores/appStore.ts — Zustand global state store.
 *
 * Covers:
 * - Initial state values
 * - toggleTheme() switches between dark/light
 * - toggleSidebar() toggles sidebar state
 * - setRefreshInterval() updates interval
 */
import { describe, it, expect, beforeEach } from "vitest";
import { useAppStore } from "@/stores/appStore";

describe("appStore", () => {
  beforeEach(() => {
    // Reset store to defaults before each test
    useAppStore.setState({
      theme: "dark",
      sidebarOpen: true,
      refreshInterval: 30000,
    });
  });

  it("has correct initial state", () => {
    const state = useAppStore.getState();
    expect(state.theme).toBe("dark");
    expect(state.sidebarOpen).toBe(true);
    expect(state.refreshInterval).toBe(30000);
  });

  it("toggleTheme switches dark to light", () => {
    useAppStore.getState().toggleTheme();
    expect(useAppStore.getState().theme).toBe("light");
  });

  it("toggleTheme switches light back to dark", () => {
    useAppStore.getState().toggleTheme(); // → light
    useAppStore.getState().toggleTheme(); // → dark
    expect(useAppStore.getState().theme).toBe("dark");
  });

  it("toggleSidebar closes when open", () => {
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarOpen).toBe(false);
  });

  it("toggleSidebar opens when closed", () => {
    useAppStore.getState().toggleSidebar(); // → false
    useAppStore.getState().toggleSidebar(); // → true
    expect(useAppStore.getState().sidebarOpen).toBe(true);
  });

  it("setRefreshInterval updates interval", () => {
    useAppStore.getState().setRefreshInterval(60000);
    expect(useAppStore.getState().refreshInterval).toBe(60000);
  });
});
