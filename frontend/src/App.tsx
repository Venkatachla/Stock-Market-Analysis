import React, { Suspense, lazy } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/contexts/AuthContext";
import AppLayout from "@/components/layout/AppLayout";
import ProtectedRoute from "@/components/ProtectedRoute";
import { LoadingState } from "@/components/common/StatusComponents";
import NotFound from "./pages/NotFound.tsx";

const Home = lazy(() => import("./pages/Home"));
const Login = lazy(() => import("./pages/Login"));
const Signup = lazy(() => import("./pages/Signup"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const StockDetail = lazy(() => import("./pages/StockDetail"));
const Discovery = lazy(() => import("./pages/Discovery"));
const Portfolio = lazy(() => import("./pages/Portfolio"));
const RiskOS = lazy(() => import("./pages/RiskOS"));

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Suspense fallback={<LoadingState />}>
            <Routes>
              {/* Public Routes */}
              <Route path="/home" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />

              {/* Protected Routes */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <Dashboard />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route path="/dashboard" element={<Navigate to="/" replace />} />
              <Route
                path="/stock/:symbol"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <StockDetail />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/discovery"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <Discovery />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/portfolio"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <Portfolio />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/risk"
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <RiskOS />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />

              {/* Fallback */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
