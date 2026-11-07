import React from "react";
import {
  LayoutDashboard,
  Files,
  Receipt,
  AlertTriangle,
  Bot,
  History,
  ShieldCheck,
  Building2,
  Shuffle,
  BookOpen,
  Sliders,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function Sidebar({ currentModule, onSelectModule }) {
  const { tenant, createRandomTenant, isLoading } = useAuth();

  const navItems = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: LayoutDashboard,
      badge: null,
      desc: "AP Risk Overview",
    },
    {
      id: "documents",
      label: "Document Ingestion",
      icon: Files,
      badge: "Queue",
      desc: "Invoices, Quotes, POs",
    },
    {
      id: "invoices",
      label: "Commercial Records",
      icon: Receipt,
      badge: null,
      desc: "Extracted Invoices",
    },
    {
      id: "findings",
      label: "Audit Findings",
      icon: AlertTriangle,
      badge: "Review",
      desc: "Anomalies & Frauds",
    },
    {
      id: "rules",
      label: "Rules & Policy Builder",
      icon: Sliders,
      badge: "Custom",
      desc: "Tenant Limits & Rules",
    },
    {
      id: "assistant",
      label: "AI Audit Assistant",
      icon: Bot,
      badge: "Gemini",
      desc: "RAG with Citations",
    },
    {
      id: "audit-logs",
      label: "Immutable Audit Trail",
      icon: History,
      badge: null,
      desc: "Compliance & Actions",
    },
    {
      id: "docs",
      label: "User Guide & Docs",
      icon: BookOpen,
      badge: "Manual",
      desc: "Step-by-Step Help",
    },
  ];

  return (
    <aside className="w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col h-screen select-none shrink-0 transition-colors">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-brand-500/25 shrink-0">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-slate-900 dark:text-slate-100 tracking-tight">AuditFlow AI</span>
            <span className="text-[10px] font-semibold bg-brand-500/20 text-brand-600 dark:text-brand-300 border border-brand-500/30 px-1.5 py-0.5 rounded">
              MVP
            </span>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400">AP Audit & Fraud Detection</p>
        </div>
      </div>

      {/* Navigation Modules */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
          Core AP Modules
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentModule === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectModule(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all group ${
                isActive
                  ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? "text-white" : "text-slate-500 dark:text-slate-400 group-hover:text-brand-600 dark:group-hover:text-brand-400"
                  }`}
                />
                <div className="text-left">
                  <div className="leading-tight">{item.label}</div>
                  <div
                    className={`text-[10px] leading-tight ${
                      isActive ? "text-brand-100 dark:text-brand-200" : "text-slate-400 dark:text-slate-500"
                    }`}
                  >
                    {item.desc}
                  </div>
                </div>
              </div>

              {item.badge && (
                <span
                  className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-semibold ${
                    isActive
                      ? "bg-white/20 text-white"
                      : "bg-slate-100 dark:bg-slate-800 text-brand-600 dark:text-brand-300 border border-slate-200 dark:border-slate-700"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Active Multi-Tenant Context Box */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/50">
        <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200">
              <Building2 className="w-3.5 h-3.5 text-brand-500 dark:text-brand-400" />
              <span className="truncate max-w-[120px]">{tenant?.name || "Active Tenant"}</span>
            </div>
            <span className="text-[9px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 px-1 py-0.2 rounded font-mono font-semibold">
              ISOLATED
            </span>
          </div>

          <div className="text-[10px] text-slate-400 dark:text-slate-500 font-mono truncate" title={tenant?.id}>
            ID: {tenant?.id ? `${tenant.id.slice(0, 10)}...` : "Loading..."}
          </div>

          <button
            onClick={() => createRandomTenant()}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-1.5 py-1.5 px-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-brand-900/40 text-slate-700 dark:text-slate-300 hover:text-brand-600 dark:hover:text-brand-300 border border-slate-200 dark:border-slate-700/80 rounded text-[11px] font-medium transition"
            title="Create and switch to a clean isolated tenant"
          >
            <Shuffle className="w-3 h-3 text-brand-500 dark:text-brand-400" />
            <span>Generate New Tenant</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
