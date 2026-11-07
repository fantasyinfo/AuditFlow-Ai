import React, { useState, useEffect } from "react";
import {
  History,
  ShieldCheck,
  Code,
  X,
  RefreshCw,
  User,
  Clock,
  ArrowRight,
} from "lucide-react";
import { api } from "../../api/client";

export default function AuditLogsModule() {
  const [logs, setLogs] = useState([]);
  const [selectedLog, setSelectedLog] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const data = await api.auditLogs.list(100);
      setLogs(data);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <History className="w-5 h-5 text-brand-600 dark:text-brand-400" />
            <span>Immutable Audit Log Trail</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Append-only non-repudiation ledger of all compliance and review operations.
          </p>
        </div>

        <button
          onClick={fetchLogs}
          className="p-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 transition flex items-center gap-1.5 text-xs font-medium"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Trail</span>
        </button>
      </div>

      {/* Audit Log Table */}
      <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
            <thead className="bg-slate-50 dark:bg-slate-950/70 uppercase text-[10px] text-slate-500 dark:text-slate-400 font-semibold tracking-wider border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Entity</th>
                <th className="py-3 px-4">Entity ID</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">State Diff</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400 text-xs">
                    Loading audit trail...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400 dark:text-slate-500 text-xs">
                    No audit actions recorded yet in this tenant.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition">
                    <td className="py-3 px-4 font-mono font-medium text-emerald-600 dark:text-emerald-400">
                      {log.action}
                    </td>
                    <td className="py-3 px-4 uppercase text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                      {log.entity}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                      {log.entity_id ? `${log.entity_id.slice(0, 10)}...` : "N/A"}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                      {log.user_id ? `${log.user_id.slice(0, 8)}...` : "System / Worker"}
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-500 dark:text-slate-400">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-brand-600 dark:text-brand-300 rounded text-[11px] font-medium transition inline-flex items-center gap-1.5"
                      >
                        <Code className="w-3 h-3" />
                        <span>Inspect Diff</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* State Diff Modal */}
      {selectedLog && (
        <div className="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-2xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Code className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 font-mono">
                  {selectedLog.action}
                </h3>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="space-y-1.5">
                <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">
                  Before State
                </span>
                <pre className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-rose-700 dark:text-rose-300 font-mono text-[11px] overflow-x-auto max-h-56">
                  {selectedLog.before_state
                    ? JSON.stringify(selectedLog.before_state, null, 2)
                    : "null"}
                </pre>
              </div>

              <div className="space-y-1.5">
                <span className="text-[10px] text-slate-500 dark:text-slate-400 uppercase font-semibold">
                  After State
                </span>
                <pre className="p-3 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-emerald-700 dark:text-emerald-300 font-mono text-[11px] overflow-x-auto max-h-56">
                  {selectedLog.after_state
                    ? JSON.stringify(selectedLog.after_state, null, 2)
                    : "null"}
                </pre>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

