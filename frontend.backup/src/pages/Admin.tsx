import { useEffect, useState } from "react";
import axios from "axios";
import { AppLayout } from "@/components/AppLayout";

const API_URL = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";
const SETTINGS_KEY = "trading_controls_v1";

interface TradingControls {
  riskPerTrade: number;
  maxTradesPerDay: number;
  swingEnabled: boolean;
  intradayEnabled: boolean;
  confidenceThreshold: number;
}

const defaultControls: TradingControls = {
  riskPerTrade: 1,
  maxTradesPerDay: 5,
  swingEnabled: true,
  intradayEnabled: true,
  confidenceThreshold: 70,
};

const Admin = () => {
  const [controls, setControls] = useState<TradingControls>(defaultControls);
  const [status, setStatus] = useState("");

  useEffect(() => {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) {
      try {
        setControls(JSON.parse(raw));
      } catch {
        setControls(defaultControls);
      }
    }

    const load = async () => {
      try {
        const response = await axios.get(`${API_URL}/settings`);
        const data = response.data;
        if (!data) return;

        setControls((prev) => ({
          ...prev,
          riskPerTrade: Number(data.risk_per_trade ?? prev.riskPerTrade),
          maxTradesPerDay: Number(data.max_trades_per_day ?? prev.maxTradesPerDay),
          swingEnabled: Boolean(data.swing_enabled ?? prev.swingEnabled),
          intradayEnabled: Boolean(data.intraday_enabled ?? prev.intradayEnabled),
          confidenceThreshold: Number(data.confidence_threshold ?? prev.confidenceThreshold),
        }));
      } catch {
        // local-only fallback is acceptable
      }
    };

    load();
  }, []);

  const save = async () => {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(controls));

    try {
      await axios.post(`${API_URL}/settings`, {
        risk_per_trade: controls.riskPerTrade,
        max_trades_per_day: controls.maxTradesPerDay,
        swing_enabled: controls.swingEnabled,
        intraday_enabled: controls.intradayEnabled,
        confidence_threshold: controls.confidenceThreshold,
      });
    } catch {
      // Keep local save even if backend setting endpoint is unavailable.
    }

    setStatus("Saved");
  };

  return (
    <AppLayout>
      <div className="space-y-6 max-w-3xl">
        <div>
          <h1>CONTROL PANEL</h1>
          <p className="text-sm text-muted-foreground mt-1">Simple risk and execution controls</p>
        </div>

        {status && <div className="rounded-md border border-green-500/30 bg-green-500/10 px-3 py-2 text-sm text-green-300">{status}</div>}

        <div className="rounded-xl border border-border/60 bg-card p-5 space-y-6">
          <div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span>Risk per trade</span>
              <span className="font-mono-data">{controls.riskPerTrade.toFixed(1)}%</span>
            </div>
            <input
              type="range"
              min={0.5}
              max={5}
              step={0.1}
              value={controls.riskPerTrade}
              onChange={(e) => setControls((p) => ({ ...p, riskPerTrade: Number(e.target.value) }))}
              className="w-full"
            />
          </div>

          <div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span>Max trades per day</span>
              <span className="font-mono-data">{controls.maxTradesPerDay}</span>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              step={1}
              value={controls.maxTradesPerDay}
              onChange={(e) => setControls((p) => ({ ...p, maxTradesPerDay: Number(e.target.value) }))}
              className="w-full"
            />
          </div>

          <div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span>Confidence threshold</span>
              <span className="font-mono-data">{controls.confidenceThreshold}%</span>
            </div>
            <input
              type="range"
              min={50}
              max={95}
              step={1}
              value={controls.confidenceThreshold}
              onChange={(e) => setControls((p) => ({ ...p, confidenceThreshold: Number(e.target.value) }))}
              className="w-full"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              onClick={() => setControls((p) => ({ ...p, intradayEnabled: !p.intradayEnabled }))}
              className={`px-3 py-2 rounded-md border text-sm font-semibold ${controls.intradayEnabled ? "border-green-500/30 bg-green-500/15 text-green-300" : "border-red-500/30 bg-red-500/15 text-red-300"}`}
            >
              Intraday {controls.intradayEnabled ? "ON" : "OFF"}
            </button>

            <button
              onClick={() => setControls((p) => ({ ...p, swingEnabled: !p.swingEnabled }))}
              className={`px-3 py-2 rounded-md border text-sm font-semibold ${controls.swingEnabled ? "border-green-500/30 bg-green-500/15 text-green-300" : "border-red-500/30 bg-red-500/15 text-red-300"}`}
            >
              Swing {controls.swingEnabled ? "ON" : "OFF"}
            </button>
          </div>

          <button
            onClick={save}
            className="w-full rounded-md bg-primary text-primary-foreground py-2 text-sm font-semibold hover:bg-primary/90"
          >
            Save Controls
          </button>
        </div>
      </div>
    </AppLayout>
  );
};

export default Admin;
