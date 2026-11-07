import React, { useState, useEffect } from "react";
import {
  Activity,
  LogOut,
  User,
  ShieldAlert,
  Sparkles,
  Server,
  Sun,
  Moon,
  BookOpen,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";
import { api } from "../../api/client";

export default function Navbar({ currentModuleTitle, onNavigateDocs }) {
  const { currentUser, tenant, logout } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();
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
    <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/70 backdrop-blur-md px-6 flex items-center justify-between z-10 transition-colors">
      {/* Current Screen Title */}
      <div className="flex items-center gap-3">
        <h1 className="text-base font-bold text-slate-900 dark:text-slate-100 tracking-tight">
          {currentModuleTitle}
        </h1>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Backend & pgvector Live Health Badge */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 text-[11px]">
          <span
            className={`w-2 h-2 rounded-full ${
              health.status === "online"
                ? "bg-emerald-500 animate-pulse"
                : health.status === "checking"
                ? "bg-amber-400"
                : "bg-rose-500"
            }`}
          />
          <span className="text-slate-600 dark:text-slate-400">
            {health.status === "online"
              ? "FastAPI & pgvector Ready"
              : health.status === "checking"
              ? "Verifying stack..."
              : "Backend Offline"}
          </span>
        </div>

        {/* User Guide Button */}
        {onNavigateDocs && (
          <button
            onClick={onNavigateDocs}
            className="flex items-center gap-1.5 py-1.5 px-2.5 rounded-lg text-slate-600 dark:text-slate-300 hover:text-brand-600 dark:hover:text-brand-400 bg-slate-100 dark:bg-slate-800/80 hover:bg-slate-200 dark:hover:bg-slate-800 text-xs font-medium border border-slate-200 dark:border-slate-700/80 transition"
            title="Read User Guide & Module Documentation"
          >
            <BookOpen className="w-3.5 h-3.5 text-brand-500" />
            <span className="hidden md:inline">Guide & Docs</span>
          </button>
        )}

        {/* Light / Dark Mode Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
          title={`Switch to ${isDark ? "Light" : "Dark"} Theme`}
        >
          {isDark ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-slate-700" />
          )}
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-200 dark:border-slate-800">
          <div className="text-right hidden md:block">
            <div className="text-xs font-semibold text-slate-900 dark:text-slate-200">
              {currentUser?.email || "Auditor"}
            </div>
            <div className="text-[10px] text-brand-600 dark:text-brand-400 font-medium uppercase tracking-wider">
              {currentUser?.role || "Admin"} • {tenant?.name || "Tenant"}
            </div>
          </div>

          <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-300">
            <User className="w-4 h-4 text-brand-500" />
          </div>

          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 dark:hover:text-rose-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
