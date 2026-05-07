/**
 * Tests for src/pages/NotFound.tsx — 404 error page.
 *
 * Covers:
 * - Renders 404 heading
 * - Renders "Page not found" message
 * - Renders link back to home page
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import NotFound from "@/pages/NotFound";

// NotFound uses useLocation, so must be wrapped in a Router
function renderNotFound() {
  return render(
    <MemoryRouter initialEntries={["/nonexistent"]}>
      <NotFound />
    </MemoryRouter>
  );
}

describe("NotFound", () => {
  it("renders 404 heading", () => {
    renderNotFound();
    expect(screen.getByText("404")).toBeTruthy();
  });

  it("renders page not found message", () => {
    renderNotFound();
    expect(screen.getByText(/page not found/i)).toBeTruthy();
  });

  it("renders return to home link", () => {
    renderNotFound();
    const link = screen.getByText(/return to home/i);
    expect(link).toBeTruthy();
    expect(link.getAttribute("href")).toBe("/");
  });
});
