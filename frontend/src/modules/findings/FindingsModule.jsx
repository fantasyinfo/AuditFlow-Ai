import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Filter,
  Check,
  X,
  FileText,
  Clock,
  RefreshCw,
  MessageSquare,
} from "lucide-react";
import { api } from "../../api/client";

export default function FindingsModule() {
  const [findings, setFindings] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [ruleFilter, setRuleFilter] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  // Review Modal State
  const [reviewFinding, setReviewFinding] = useState(null);
  const [reviewAction, setReviewAction] = useState(""); // "confirmed" or "dismissed"
  const [reviewNotes, setReviewNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchFindings = async () => {
    setIsLoading(true);
    try {
      const data = await api.findings.list(statusFilter, ruleFilter, 100);
      setFindings(data);
    } catch (err) {
      console.error("Failed to load findings:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, [statusFilter, ruleFilter]);

  const openReviewModal = (finding, action) => {
    setReviewFinding(finding);
    setReviewAction(action);
    setReviewNotes(`Auditor assessment on ${new Date().toLocaleDateString()}`);
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!reviewFinding || !reviewAction) return;

    setIsSubmitting(true);
    try {
      await api.findings.update(reviewFinding.id, reviewAction, reviewNotes);
      setReviewFinding(null);
      fetchFindings();
    } catch (err) {
      alert(err.message || "Failed to update finding status");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500 dark:text-amber-400" />
            <span>Audit Findings & Review Center</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Deterministic rule violations requiring human finance verification.
          </p>
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg py-1.5 px-3 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Statuses</option>
            <option value="open">Open (Unreviewed)</option>
            <option value="confirmed">Confirmed</option>
            <option value="dismissed">Dismissed</option>
          </select>

          <select
            value={ruleFilter}
            onChange={(e) => setRuleFilter(e.target.value)}
            className="bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg py-1.5 px-3 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Audit Rules</option>
            <option value="duplicate_invoice">Duplicate Invoice</option>
            <option value="amount_mismatch">Amount Mismatch</option>
            <option value="missing_evidence">Missing Evidence</option>
            <option value="invalid_gstin">Invalid GSTIN</option>
            <option value="unusual_amount">Unusual Amount</option>
          </select>

          <button
            onClick={fetchFindings}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 transition"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Findings Table */}
      <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
            <thead className="bg-slate-50 dark:bg-slate-950/70 uppercase text-[10px] text-slate-500 dark:text-slate-400 font-semibold tracking-wider border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-3 px-4">Rule Violation</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Reason & Details</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Identified At</th>
                <th className="py-3 px-4 text-right">Auditor Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400 text-xs">
                    Loading audit findings...
                  </td>
                </tr>
              ) : findings.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400 dark:text-slate-500 text-xs">
                    No findings recorded matching the selected filters.
                  </td>
                </tr>
              ) : (
                findings.map((f) => {
                  let sevBadge = "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300";
                  if (f.severity === "critical") {
                    sevBadge = "bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20 font-bold";
                  } else if (f.severity === "high") {
                    sevBadge = "bg-orange-500/10 text-orange-700 dark:text-orange-300 border border-orange-500/20";
                  } else if (f.severity === "medium") {
                    sevBadge = "bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20";
                  }

                  return (
                    <tr key={f.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-mono font-medium text-brand-600 dark:text-brand-300">
                        {f.rule}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase ${sevBadge}`}>
                          {f.severity}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-800 dark:text-slate-200 max-w-md">
                        <p className="leading-snug">{f.reason}</p>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-semibold uppercase tracking-wider ${
                            f.status === "open"
                              ? "bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20"
                              : f.status === "confirmed"
                              ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20"
                              : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                          }`}
                        >
                          {f.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-500 dark:text-slate-400 text-[11px]">
                        {new Date(f.created_at).toLocaleTimeString()}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {f.status === "open" ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => openReviewModal(f, "confirmed")}
                              className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-semibold transition"
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => openReviewModal(f, "dismissed")}
                              className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded text-[11px] font-semibold transition"
                            >
                              Dismiss
                            </button>
                          </div>
                        ) : (
                          <span className="text-[11px] text-slate-400 dark:text-slate-500 italic">
                            Reviewed
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review Modal */}
      {reviewFinding && (
        <div className="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                <span>
                  {reviewAction === "confirmed" ? "Confirm Finding" : "Dismiss Finding"}
                </span>
              </h3>
              <button
                onClick={() => setReviewFinding(null)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-1 text-xs">
              <span className="text-slate-500 dark:text-slate-400">Rule:</span>
              <p className="font-mono text-brand-600 dark:text-brand-300 font-semibold">{reviewFinding.rule}</p>
              <p className="text-slate-700 dark:text-slate-300 pt-1 text-[11px]">{reviewFinding.reason}</p>
            </div>

            <form onSubmit={handleReviewSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="block text-xs font-medium text-slate-600 dark:text-slate-400">
                  Auditor Review Notes (Written to Immutable Audit Trail)
                </label>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Explain rationale for confirming or dismissing this finding..."
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2.5 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-brand-500"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setReviewFinding(null)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={`px-4 py-2 text-white rounded-lg text-xs font-semibold transition ${
                    reviewAction === "confirmed"
                      ? "bg-emerald-600 hover:bg-emerald-500"
                      : "bg-slate-700 hover:bg-slate-600"
                  }`}
                >
                  {isSubmitting ? "Submitting..." : `Confirm as ${reviewAction}`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

