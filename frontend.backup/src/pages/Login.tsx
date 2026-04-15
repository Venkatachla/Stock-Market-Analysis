import { useState } from "react";
import axios from "axios";
import { AppLayout } from "@/components/AppLayout";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [status, setStatus] = useState("");

  const submit = async () => {
    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
      const res = await axios.post(`${API_URL}${endpoint}`, { email, password });
      localStorage.setItem("auth_token", res.data.token);
      localStorage.setItem("user_tier", res.data.tier);
      setStatus(`Success: ${mode} completed. Tier: ${res.data.tier}`);
    } catch (e: any) {
      setStatus(`Error: ${e?.response?.data?.detail || e.message}`);
    }
  };

  return (
    <AppLayout>
      <div className="max-w-md mx-auto mt-10 stat-card space-y-4">
        <h1 className="text-xl font-bold">Account Access</h1>
        <p className="text-sm text-muted-foreground">Login for paid signals and advanced analytics.</p>

        <div className="flex gap-2">
          <button className={`px-3 py-1.5 rounded ${mode === "login" ? "bg-primary text-primary-foreground" : "bg-muted"}`} onClick={() => setMode("login")}>Login</button>
          <button className={`px-3 py-1.5 rounded ${mode === "register" ? "bg-primary text-primary-foreground" : "bg-muted"}`} onClick={() => setMode("register")}>Register</button>
        </div>

        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" className="w-full px-3 py-2 rounded border border-border bg-black text-white" />
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="Password" className="w-full px-3 py-2 rounded border border-border bg-black text-white" />

        <button onClick={submit} className="w-full px-3 py-2 rounded bg-primary text-primary-foreground">{mode === "login" ? "Login" : "Create Account"}</button>

        {status && <p className="text-xs text-muted-foreground">{status}</p>}
      </div>
    </AppLayout>
  );
};

export default Login;
