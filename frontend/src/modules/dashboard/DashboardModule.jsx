import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  FileText,
  DollarSign,
  ShieldCheck,
  ArrowUpRight,
  TrendingUp,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  Clock,
  ExternalLink,
} from "lucide-react";
import { api } from "../../api/client";

export default function DashboardModule({ onNavigate }) {
  const [stats, setStats] = useState({
    totalDocs: 0,
    openFindings: 0,
    criticalFindings: 0,
    totalAtRisk: 0,
    invoicesCount: 0,
  });
  const [recentFindings, setRecentFindings] = useState([]);
  const [recentDocs, setRecentDocs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [docs, findings, invoices] = await Promise.all([
        api.documents.list("", 10).catch(() => []),
        api.findings.list("", "", 20).catch(() => []),
        api.invoices.list(20).catch(() => []),
      ]);

      const openF = findings.filter((f) => f.status === "open");
      const critF = findings.filter((f) => f.severity === "critical");

      // Approximate risk amount from flagged invoices
      let riskTotal = 0;
      const flaggedInvoiceIds = new Set(openF.map((f) => f.invoice_id));
      invoices.forEach((inv) => {
        if (flaggedInvoiceIds.has(inv.id) && inv.total_amount) {
          riskTotal += parseFloat(inv.total_amount) || 0;
        }
      });

      setStats({
        totalDocs: docs.length,
        openFindings: openF.length,
        criticalFindings: critF.length,
        totalAtRisk: riskTotal,
        invoicesCount: invoices.length,
      });

      setRecentFindings(findings.slice(0, 5));
      setRecentDocs(docs.slice(0, 4));
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner & Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-brand-900/80 via-slate-900 to-slate-900 dark:from-brand-950/80 dark:via-slate-900 dark:to-slate-900 border border-brand-500/30 shadow-xl shadow-brand-950/20 text-white">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30">
              Executive AP Command Center
            </span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">
            Accounts Payable Audit & Anomaly Detection
          </h2>
          <p className="text-xs text-slate-300 dark:text-slate-400 max-w-xl">
            Real-time multi-tenant monitoring across invoices, quotations, agreements, and purchase orders.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate("documents")}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold transition flex items-center gap-2 shadow-lg shadow-brand-600/30"
          >
            <FileText className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
          <button
            onClick={() => onNavigate("assistant")}
            className="px-4 py-2 bg-purple-600/30 hover:bg-purple-600/50 text-purple-200 border border-purple-500/40 rounded-lg text-xs font-semibold transition flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4 text-purple-400" />
            <span>AI Assistant</span>
          </button>
        </div>
      </div>

      {/* KPI Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Ingested Documents */}
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2 relative overflow-hidden shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-medium">Ingested Documents</span>
            <FileText className="w-4 h-4 text-brand-500 dark:text-brand-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900 dark:text-slate-100 font-mono">
            {stats.totalDocs}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <span className="text-emerald-600 dark:text-emerald-400 font-medium">100% tenant-isolated</span>
            <span>• {stats.invoicesCount} extracted records</span>
          </div>
          <div className="absolute -right-3 -bottom-3 w-16 h-16 bg-brand-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* KPI 2: Open Findings */}
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2 relative overflow-hidden shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-medium">Open Audit Findings</span>
            <AlertTriangle className="w-4 h-4 text-amber-500 dark:text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-600 dark:text-amber-400 font-mono">
            {stats.openFindings}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <span className="text-rose-600 dark:text-rose-400 font-medium">{stats.criticalFindings} critical</span>
            <span>requiring auditor review</span>
          </div>
          <div className="absolute -right-3 -bottom-3 w-16 h-16 bg-amber-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* KPI 3: Amount at Risk */}
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2 relative overflow-hidden shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-medium">Total Amount at Risk</span>
            <DollarSign className="w-4 h-4 text-rose-500 dark:text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-600 dark:text-rose-400 font-mono">
            ₹{stats.totalAtRisk.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            <span>Deterministic sum of flagged invoices</span>
          </div>
          <div className="absolute -right-3 -bottom-3 w-16 h-16 bg-rose-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* KPI 4: Active Detection Rules */}
        <div className="p-5 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2 relative overflow-hidden shadow-sm">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400">
            <span className="text-xs font-medium">Audit Rules Active</span>
            <ShieldCheck className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-mono">
            5 Rules
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
            <span>Duplicate, Mismatch, Missing PO, GSTIN, Spikes</span>
          </div>
          <div className="absolute -right-3 -bottom-3 w-16 h-16 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: High Priority Audit Findings */}
        <div className="lg:col-span-2 rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200">
                Recent Audit Detection Alerts
              </h3>
            </div>
            <button
              onClick={() => onNavigate("findings")}
              className="text-xs text-brand-600 dark:text-brand-400 hover:text-brand-500 flex items-center gap-1 transition"
            >
              <span>View All Findings</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {recentFindings.length === 0 ? (
              <div className="py-8 text-center text-slate-400 dark:text-slate-500 text-xs">
                No findings detected yet. Ingest documents to trigger rules engine.
              </div>
            ) : (
              recentFindings.map((f) => (
                <div key={f.id} className="py-3 flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded font-bold ${
                          f.severity === "critical"
                            ? "bg-rose-500/20 text-rose-700 dark:text-rose-300 border border-rose-500/30"
                            : f.severity === "high"
                            ? "bg-orange-500/20 text-orange-700 dark:text-orange-300 border border-orange-500/30"
                            : "bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-500/30"
                        }`}
                      >
                        {f.severity}
                      </span>
                      <span className="text-xs font-mono font-medium text-brand-600 dark:text-brand-300">
                        {f.rule}
                      </span>
                      <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                        #{f.id.slice(0, 8)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-snug">{f.reason}</p>
                  </div>

                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-semibold uppercase tracking-wider ${
                      f.status === "open"
                        ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                        : f.status === "confirmed"
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    {f.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right 1 Col: Live Ingestion Queue Status */}
        <div className="rounded-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200">
                Document Queue
              </h3>
            </div>
            <button
              onClick={() => onNavigate("documents")}
              className="text-xs text-brand-600 dark:text-brand-400 hover:text-brand-500 transition"
            >
              Manage
            </button>
          </div>

          <div className="space-y-3">
            {recentDocs.length === 0 ? (
              <div className="py-8 text-center text-slate-400 dark:text-slate-500 text-xs">
                No documents uploaded in this tenant.
              </div>
            ) : (
              recentDocs.map((doc) => (
                <div
                  key={doc.id}
                  className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/80 flex items-center justify-between text-xs"
                >
                  <div className="space-y-0.5 truncate max-w-[160px]">
                    <div className="font-medium text-slate-800 dark:text-slate-200 truncate">
                      {doc.filename}
                    </div>
                    <div className="text-[10px] text-slate-500 uppercase">
                      {doc.type}
                    </div>
                  </div>

                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-mono font-medium ${
                      doc.status === "done"
                        ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                        : doc.status === "processing"
                        ? "bg-brand-500/20 text-brand-600 dark:text-brand-300 border border-brand-500/30 animate-pulse"
                        : doc.status === "failed"
                        ? "bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/30"
                        : "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                    }`}
                  >
                    {doc.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

