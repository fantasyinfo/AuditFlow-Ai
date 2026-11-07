import React, { useState, useEffect } from "react";
import {
  Activity,
  LogOut,
  User,
  ShieldAlert,
  Sparkles,
  Server,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../api/client";

export default function Navbar({ currentModuleTitle }) {
  const { currentUser, tenant, logout } = useAuth();
  const [health, setHealth] = useState({ status: "checking", db: "checking" });

  useEffect(() => {
    let isMounted = true;
    const checkApiHealth = async () => {
      try {
        const res = await api.health.check();
        if (isMounted) {
          setHealth({
            status: res.status === "healthy" ? "online" : "degraded",
            db: res.database || "connected",
          });
        }
      } catch (err) {
        if (isMounted) {
          setHealth({ status: "offline", db: "unreachable" });
        }
      }
    };

    checkApiHealth();
    const interval = setInterval(checkApiHealth, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 flex items-center justify-between z-10">
      {/* Current Screen Title */}
      <div className="flex items-center gap-3">
        <h1 className="text-base font-bold text-slate-100 tracking-tight">
          {currentModuleTitle}
        </h1>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* Backend & pgvector Live Health Badge */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-950/80 border border-slate-800 text-[11px]">
          <span
            className={`w-2 h-2 rounded-full ${
              health.status === "online"
                ? "bg-emerald-400 animate-pulse"
                : health.status === "checking"
                ? "bg-amber-400"
                : "bg-rose-500"
            }`}
          />
          <span className="text-slate-400">
            {health.status === "online"
              ? "FastAPI & pgvector Ready"
              : health.status === "checking"
              ? "Verifying stack..."
              : "Backend Offline"}
          </span>
        </div>

        {/* User Profile */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-800">
          <div className="text-right hidden md:block">
            <div className="text-xs font-semibold text-slate-200">
              {currentUser?.email || "Auditor"}
            </div>
            <div className="text-[10px] text-brand-400 font-medium uppercase tracking-wider">
              {currentUser?.role || "Admin"} • {tenant?.name || "Tenant"}
            </div>
          </div>

          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300">
            <User className="w-4 h-4 text-brand-400" />
          </div>

          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
