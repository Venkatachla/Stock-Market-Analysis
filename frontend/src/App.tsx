import React, { Suspense, lazy } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import AppLayout from "@/components/layout/AppLayout";
import { LoadingState } from "@/components/common/StatusComponents";
import NotFound from "./pages/NotFound.tsx";

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
      <BrowserRouter>
        <AppLayout>
          <Suspense fallback={<LoadingState />}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/stock/:symbol" element={<StockDetail />} />
              <Route path="/discovery" element={<Discovery />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/risk" element={<RiskOS />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </AppLayout>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
