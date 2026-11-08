import React from "react";
import {
  LayoutDashboard,
  FolderKanban,
  Files,
  Receipt,
  Scale,
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

  const navSections = [
    {
      title: "Workspace",
      items: [
        { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
        { id: "projects", label: "Projects", icon: FolderKanban },
        { id: "documents", label: "Documents", icon: Files },
        { id: "invoices", label: "Commercial Records", icon: Receipt },
        { id: "reconciliation", label: "Reconciliation", icon: Scale },
      ],
    },
    {
      title: "Audit & Controls",
      items: [
        { id: "findings", label: "Audit Findings", icon: AlertTriangle },
        { id: "rules", label: "Rules & Policies", icon: Sliders },
        { id: "assistant", label: "AI Assistant", icon: Bot },
        { id: "audit-logs", label: "Audit Trail", icon: History },
      ],
    },
    {
      title: "Resources",
      items: [
        { id: "docs", label: "Documentation", icon: BookOpen },
      ],
    },
  ];

  return (
    <aside className="w-60 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col h-screen select-none shrink-0 transition-colors">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white shadow-sm shrink-0">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-sm text-slate-900 dark:text-slate-100 tracking-tight truncate">
              AuditFlow AI
            </span>
            <span className="text-[10px] font-semibold bg-brand-500/10 text-brand-600 dark:text-brand-300 border border-brand-500/20 px-1 py-0.2 rounded">
              MVP
            </span>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">AP Audit & Fraud Detection</p>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto p-3 space-y-5">
        {navSections.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {section.title}
            </div>
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = currentModule === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectModule(item.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? "bg-brand-50 dark:bg-brand-500/15 text-brand-700 dark:text-brand-300 font-semibold border border-brand-200 dark:border-brand-500/30"
                      : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/60"
                  }`}
                >
                  <Icon
                    className={`w-4 h-4 shrink-0 transition-colors ${
                      isActive
                        ? "text-brand-600 dark:text-brand-400"
                        : "text-slate-400 dark:text-slate-500 group-hover:text-slate-600 dark:group-hover:text-slate-300"
                    }`}
                  />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Active Multi-Tenant Context Box */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/40">
        <div className="p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1.5 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200">
              <Building2 className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400 shrink-0" />
              <span className="truncate max-w-[110px]">{tenant?.name || "Active Tenant"}</span>
            </div>
            <span className="text-[9px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 px-1 py-0.2 rounded font-mono font-semibold">
              ISOLATED
            </span>
          </div>

          <button
            onClick={() => createRandomTenant()}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-1.5 py-1 px-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-750 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 rounded text-[11px] font-medium transition"
            title="Create and switch to a clean isolated tenant"
          >
            <Shuffle className="w-3 h-3 text-brand-600 dark:text-brand-400" />
            <span>Generate Tenant</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
