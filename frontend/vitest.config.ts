import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react-swc";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov"],
      reportsDirectory: "./coverage",
      exclude: [
        "node_modules/**",
        "dist/**",
        "src/components/ui/**",
        "src/lib/**",
        "src/hooks/use-mobile.tsx",
        "src/main.tsx",
        "src/App.tsx",
        "**/*.d.ts",
        "**/*.test.ts",
        "**/*.test.tsx",
        "**/*.spec.ts",
        "**/*.spec.tsx",
        "vite.config.ts",
        "vitest.config.ts",
        "tailwind.config.ts",
        "eslint.config.js",
        "postcss.config.js",
        "src/test/setup.ts"
      ],
      thresholds: {
        lines: 10,
        functions: 10,
        branches: 10,
        statements: 10
      }
    }
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
});
