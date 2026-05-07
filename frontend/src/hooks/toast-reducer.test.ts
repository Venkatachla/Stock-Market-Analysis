/**
 * Tests for the toast reducer in src/hooks/use-toast.ts
 *
 * The reducer is exported and is a pure function — ideal for unit testing.
 *
 * Covers:
 * - ADD_TOAST: adds toast, respects TOAST_LIMIT (1)
 * - UPDATE_TOAST: updates existing toast by ID
 * - DISMISS_TOAST: dismisses specific or all toasts (sets open=false)
 * - REMOVE_TOAST: removes specific or all toasts from state
 */
import { describe, it, expect } from "vitest";
import { reducer } from "@/hooks/use-toast";

// Helper: create a minimal toast-like object
function makeToast(id: string, title = "Test") {
  return { id, title, open: true, onOpenChange: () => {} } as any;
}

describe("toast reducer", () => {
  describe("ADD_TOAST", () => {
    it("adds a toast to empty state", () => {
      const state = { toasts: [] };
      const result = reducer(state, {
        type: "ADD_TOAST",
        toast: makeToast("1"),
      });
      expect(result.toasts).toHaveLength(1);
      expect(result.toasts[0].id).toBe("1");
    });

    it("respects TOAST_LIMIT (newest first)", () => {
      // TOAST_LIMIT is 1, so adding a second toast should evict the first
      const state = { toasts: [makeToast("1")] };
      const result = reducer(state, {
        type: "ADD_TOAST",
        toast: makeToast("2"),
      });
      expect(result.toasts).toHaveLength(1);
      expect(result.toasts[0].id).toBe("2");
    });
  });

  describe("UPDATE_TOAST", () => {
    it("updates an existing toast by ID", () => {
      const state = { toasts: [makeToast("1", "Original")] };
      const result = reducer(state, {
        type: "UPDATE_TOAST",
        toast: { id: "1", title: "Updated" },
      });
      expect(result.toasts[0].title).toBe("Updated");
    });

    it("does not affect other toasts", () => {
      const state = {
        toasts: [makeToast("1", "First"), makeToast("2", "Second")],
      };
      const result = reducer(state, {
        type: "UPDATE_TOAST",
        toast: { id: "1", title: "Changed" },
      });
      expect(result.toasts.find((t) => t.id === "2")?.title).toBe("Second");
    });
  });

  describe("DISMISS_TOAST", () => {
    it("dismisses a specific toast (sets open=false)", () => {
      const state = { toasts: [makeToast("1")] };
      const result = reducer(state, {
        type: "DISMISS_TOAST",
        toastId: "1",
      });
      expect(result.toasts[0].open).toBe(false);
    });

    it("dismisses all toasts when no ID specified", () => {
      const state = {
        toasts: [makeToast("1"), makeToast("2")],
      };
      const result = reducer(state, { type: "DISMISS_TOAST" });
      for (const toast of result.toasts) {
        expect(toast.open).toBe(false);
      }
    });
  });

  describe("REMOVE_TOAST", () => {
    it("removes a specific toast by ID", () => {
      const state = {
        toasts: [makeToast("1"), makeToast("2")],
      };
      const result = reducer(state, {
        type: "REMOVE_TOAST",
        toastId: "1",
      });
      expect(result.toasts).toHaveLength(1);
      expect(result.toasts[0].id).toBe("2");
    });

    it("removes all toasts when no ID specified", () => {
      const state = {
        toasts: [makeToast("1"), makeToast("2")],
      };
      const result = reducer(state, {
        type: "REMOVE_TOAST",
        toastId: undefined,
      });
      expect(result.toasts).toHaveLength(0);
    });
  });
});
