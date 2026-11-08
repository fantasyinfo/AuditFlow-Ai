import React, { useState, useEffect } from "react";
import {
  Scale,
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Calculator,
  Percent,
  Plus,
  ArrowRight,
  Building2,
  Receipt,
  CreditCard,
  RefreshCw,
} from "lucide-react";
import { api } from "../../api/client";
import { useProject } from "../../context/ProjectContext";

export function ReconciliationModule({ onNavigate }) {
  const { projects, selectedProject, selectedProjectId, selectProject, refreshProjects } = useProject();
  const [reconciliation, setReconciliation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // View modes & toggles
  const [showNetWithoutGST, setShowNetWithoutGST] = useState(false);
  const [tdsRate, setTdsRate] = useState("2.0");
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedInvoiceForPayment, setSelectedInvoiceForPayment] = useState(null);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [submittingPayment, setSubmittingPayment] = useState(false);

  const fetchReconciliation = async (projectId) => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.projects.getReconciliation(projectId);
      setReconciliation(data);
    } catch (err) {
      setError(err.message || "Failed to load project reconciliation");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProjectId) {
      fetchReconciliation(selectedProjectId);
    } else if (projects.length > 0) {
      selectProject(projects[0].id);
    }
  }, [selectedProjectId, projects]);

  const formatCurrency = (amt, currency = "INR") => {
    const val = parseFloat(amt) || 0;
    const symbol = currency === "INR" ? "₹" : "$";
    return `${symbol}${val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const handleOpenPayment = (invoice) => {
    setSelectedInvoiceForPayment(invoice);
    setPaymentAmount(invoice.remaining_unpaid.toString());
    setShowPaymentModal(true);
  };

  const handleRecordPayment = async (e) => {
    e.preventDefault();
    if (!selectedInvoiceForPayment || !selectedProjectId) return;
    setSubmittingPayment(true);
    try {
      await api.projects.recordPayment(selectedProjectId, selectedInvoiceForPayment.id, {
        paid_amount: parseFloat(paymentAmount),
      });
      await fetchReconciliation(selectedProjectId);
      await refreshProjects();
      setShowPaymentModal(false);
      setSelectedInvoiceForPayment(null);
    } catch (err) {
      alert("Failed to record payment: " + err.message);
    } finally {
      setSubmittingPayment(false);
    }
  };

  if (projects.length === 0) {
    return (
      <div className="space-y-6">
        <div className="rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 p-10 text-center shadow-sm">
          <Scale className="mx-auto h-10 w-10 text-slate-400 dark:text-slate-600 mb-2" />
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">No Projects Configured</h3>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
            Create an audit project with an agreed quotation budget before viewing financial reconciliation.
          </p>
          <button
            onClick={() => onNavigate && onNavigate("projects")}
            className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3.5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-brand-500 transition"
          >
            <Plus className="h-4 w-4" />
            <span>Go to Projects</span>
          </button>
        </div>
      </div>
    );
  }

  const proj = reconciliation?.project || selectedProject;
  const quotedGross = parseFloat(reconciliation?.quoted_gross || 0);
  const quotedNet = parseFloat(reconciliation?.quoted_net || 0);
  const quotedGst = parseFloat(reconciliation?.quoted_gst || 0);

  const totalInvoicedGross = parseFloat(reconciliation?.total_invoiced_gross || 0);
  const totalInvoicedNet = parseFloat(reconciliation?.total_invoiced_net || 0);
  const totalInvoicedGst = parseFloat(reconciliation?.total_invoiced_gst || 0);

  const totalPaid = parseFloat(reconciliation?.total_paid_gross || 0);
  const remainingUnderQuotation = parseFloat(reconciliation?.remaining_balance_under_quotation || 0);

  const isOver = reconciliation?.is_over_logged || false;
  const varianceAmt = parseFloat(reconciliation?.variance_amount || 0);
  const variancePct = parseFloat(reconciliation?.variance_percent || 0);
  const burnRatePct = parseFloat(reconciliation?.burn_rate_percent || 0);

  // TDS simulation
  const tdsPct = parseFloat(tdsRate) || 0;
  const simulatedTds = totalInvoicedNet * (tdsPct / 100);
  const simulatedNetOutflow = totalInvoicedNet - simulatedTds;

  return (
    <div className="space-y-6">
      {/* Calm Header & Project Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 dark:bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-200 dark:border-brand-500/20">
            <Building2 className="h-4 w-4" />
          </div>
          <div>
            <span className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Audit Engagement
            </span>
            <select
              value={selectedProjectId}
              onChange={(e) => selectProject(e.target.value)}
              className="mt-0.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-2.5 py-1 text-xs font-bold text-slate-900 dark:text-slate-100 focus:outline-none"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code} — {p.name} ({p.vendor_name})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* GST Removal & View Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowNetWithoutGST(!showNetWithoutGST)}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition border ${
              showNetWithoutGST
                ? "bg-brand-600 text-white border-brand-500 shadow-sm"
                : "bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700"
            }`}
          >
            <Calculator className="h-3.5 w-3.5" />
            <span>{showNetWithoutGST ? "Viewing: Net (Ex-GST)" : "Remove GST / Net View"}</span>
          </button>

          <button
            onClick={() => fetchReconciliation(selectedProjectId)}
            className="p-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 transition"
            title="Refresh reconciliation"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {loading && !reconciliation ? (
        <div className="p-8 text-center text-xs text-slate-400">Loading reconciliation metrics...</div>
      ) : (
        <>
          {/* 4 Financial Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Quotation Baseline
              </span>
              <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
                {formatCurrency(showNetWithoutGST ? quotedNet : quotedGross)}
              </p>
              <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400 space-y-0.5">
                <div className="flex justify-between">
                  <span>Gross Quoted:</span>
                  <span className="font-mono text-slate-700 dark:text-slate-300">{formatCurrency(quotedGross)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Net (Ex-GST):</span>
                  <span className="font-mono text-brand-600 dark:text-brand-400">{formatCurrency(quotedNet)}</span>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Invoiced to Date
              </span>
              <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">
                {formatCurrency(showNetWithoutGST ? totalInvoicedNet : totalInvoicedGross)}
              </p>
              <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400 space-y-0.5">
                <div className="flex justify-between">
                  <span>Gross Billed:</span>
                  <span className="font-mono text-slate-700 dark:text-slate-300">{formatCurrency(totalInvoicedGross)}</span>
                </div>
                <div className="flex justify-between">
                  <span>GST Portion:</span>
                  <span className="font-mono text-slate-500">{formatCurrency(totalInvoicedGst)}</span>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm">
              <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider">
                <span className={isOver ? "text-rose-600 dark:text-rose-400" : "text-emerald-600 dark:text-emerald-400"}>
                  {isOver ? "Over-Logged" : "Within Budget"}
                </span>
                {isOver ? (
                  <TrendingUp className="h-3.5 w-3.5 text-rose-500" />
                ) : (
                  <TrendingDown className="h-3.5 w-3.5 text-emerald-500" />
                )}
              </div>
              <p className={`mt-1 text-2xl font-bold ${isOver ? "text-rose-600 dark:text-rose-400" : "text-slate-900 dark:text-slate-100"}`}>
                {isOver ? `+${variancePct}%` : `${variancePct}%`}
              </p>
              <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400 space-y-0.5">
                <div className="flex justify-between">
                  <span>Variance:</span>
                  <span className={`font-mono font-bold ${isOver ? "text-rose-600 dark:text-rose-400" : "text-slate-700 dark:text-slate-300"}`}>
                    {formatCurrency(varianceAmt)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Burn Rate:</span>
                  <span className="font-mono">{burnRatePct}% of cap</span>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Paid vs Balance Left
              </span>
              <p className="mt-1 text-2xl font-bold text-amber-600 dark:text-amber-400">
                {formatCurrency(remainingUnderQuotation)}
              </p>
              <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400 space-y-0.5">
                <div className="flex justify-between">
                  <span>Total Paid:</span>
                  <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">{formatCurrency(totalPaid)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Balance Left to Pay:</span>
                  <span className="font-mono text-amber-600 dark:text-amber-400 font-bold">{formatCurrency(remainingUnderQuotation)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Over-Budget Alert Pill if Over-Logged */}
          {isOver && (
            <div className="rounded-xl border border-rose-200 dark:border-rose-500/20 bg-rose-50 dark:bg-rose-950/20 p-3.5 flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5 text-rose-700 dark:text-rose-300">
                <AlertTriangle className="h-4 w-4 shrink-0 text-rose-500" />
                <span>
                  <strong>Over-Budget Warning:</strong> Invoicing for <strong>{proj?.name}</strong> has reached {formatCurrency(totalInvoicedGross)}, exceeding the quotation baseline by +{variancePct}%.
                </span>
              </div>
              <button
                onClick={() => onNavigate && onNavigate("findings")}
                className="px-2.5 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs shrink-0 transition"
              >
                View Finding
              </button>
            </div>
          )}

          {/* Compact GST Removal & Net Cash Outflow Strip */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3 mb-3">
              <div className="flex items-center gap-2">
                <Calculator className="h-4 w-4 text-brand-600 dark:text-brand-400" />
                <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">
                  GST Removal & Net Cash Outflow Breakdown
                </h3>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-500 dark:text-slate-400">Withholding TDS:</span>
                <select
                  value={tdsRate}
                  onChange={(e) => setTdsRate(e.target.value)}
                  className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 px-2 py-0.5 text-xs font-bold text-slate-800 dark:text-slate-200 focus:outline-none"
                >
                  <option value="0.0">0% (None)</option>
                  <option value="2.0">2% (Section 194C)</option>
                  <option value="10.0">10% (Section 194J)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/60">
                <span className="text-slate-400 text-[10px] uppercase font-semibold block">1. Gross Invoiced</span>
                <span className="text-sm font-bold text-slate-800 dark:text-slate-200 mt-0.5 block">{formatCurrency(totalInvoicedGross)}</span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/60">
                <span className="text-rose-500 text-[10px] uppercase font-semibold block">2. Less: GST Component</span>
                <span className="text-sm font-bold text-rose-600 dark:text-rose-400 mt-0.5 block">- {formatCurrency(totalInvoicedGst)}</span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/60">
                <span className="text-brand-600 dark:text-brand-400 text-[10px] uppercase font-semibold block">3. Net Goods/Service Base</span>
                <span className="text-sm font-bold text-brand-600 dark:text-brand-400 mt-0.5 block">{formatCurrency(totalInvoicedNet)}</span>
              </div>

              <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/60">
                <span className="text-emerald-600 dark:text-emerald-400 text-[10px] uppercase font-semibold block">4. Net Outflow (Less {tdsRate}% TDS)</span>
                <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-0.5 block">{formatCurrency(simulatedNetOutflow)}</span>
              </div>
            </div>
          </div>

          {/* Project Invoices Table */}
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
            <div className="p-3.5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Receipt className="h-4 w-4 text-brand-600 dark:text-brand-400" />
                <span>Invoices Under This Project ({reconciliation?.invoices?.length || 0})</span>
              </h3>

              <button
                onClick={() => onNavigate && onNavigate("documents")}
                className="text-xs text-brand-600 dark:text-brand-400 font-semibold hover:underline"
              >
                + Upload Invoice
              </button>
            </div>

            {(!reconciliation?.invoices || reconciliation.invoices.length === 0) ? (
              <div className="p-6 text-center text-xs text-slate-400">
                No invoices found linked to this project.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 font-semibold uppercase text-[10px]">
                    <tr>
                      <th className="py-2.5 px-4">Invoice #</th>
                      <th className="py-2.5 px-4">Date</th>
                      <th className="py-2.5 px-4 text-right">Gross Total</th>
                      <th className="py-2.5 px-4 text-right">GST (Tax)</th>
                      <th className="py-2.5 px-4 text-right font-bold text-brand-600 dark:text-brand-400">Net Base (Ex-GST)</th>
                      <th className="py-2.5 px-4 text-right">Paid</th>
                      <th className="py-2.5 px-4 text-right text-amber-600 dark:text-amber-400 font-bold">Unpaid Left</th>
                      <th className="py-2.5 px-4">Status</th>
                      <th className="py-2.5 px-4 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 font-mono text-slate-700 dark:text-slate-300">
                    {reconciliation.invoices.map((inv) => {
                      const isFullyPaid = inv.payment_status === "paid";
                      return (
                        <tr key={inv.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                          <td className="py-2.5 px-4 font-semibold text-slate-900 dark:text-slate-100 font-sans">
                            {inv.invoice_number}
                          </td>
                          <td className="py-2.5 px-4 text-slate-500 dark:text-slate-400 font-sans">{inv.invoice_date || "—"}</td>
                          <td className="py-2.5 px-4 text-right font-bold text-slate-900 dark:text-slate-100">
                            {formatCurrency(inv.total_amount)}
                          </td>
                          <td className="py-2.5 px-4 text-right text-slate-500 dark:text-slate-400">
                            {formatCurrency(inv.tax_amount)}
                          </td>
                          <td className="py-2.5 px-4 text-right font-bold text-brand-600 dark:text-brand-400">
                            {formatCurrency(inv.net_amount)}
                          </td>
                          <td className="py-2.5 px-4 text-right text-emerald-600 dark:text-emerald-400 font-bold">
                            {formatCurrency(inv.paid_amount)}
                          </td>
                          <td className="py-2.5 px-4 text-right font-bold text-amber-600 dark:text-amber-400">
                            {formatCurrency(inv.remaining_unpaid)}
                          </td>
                          <td className="py-2.5 px-4 font-sans">
                            <span
                              className={`inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-semibold uppercase ${
                                isFullyPaid
                                  ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20"
                                  : inv.paid_amount > 0
                                  ? "bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-500/20"
                                  : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                              }`}
                            >
                              {inv.payment_status}
                            </span>
                          </td>
                          <td className="py-2.5 px-4 text-center font-sans">
                            {!isFullyPaid ? (
                              <button
                                onClick={() => handleOpenPayment(inv)}
                                className="inline-flex items-center gap-1 rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 px-2 py-0.5 text-[11px] font-semibold transition"
                              >
                                <CreditCard className="h-3 w-3" />
                                <span>Record Pay</span>
                              </button>
                            ) : (
                              <span className="text-emerald-600 dark:text-emerald-400 text-xs flex items-center justify-center gap-1">
                                <CheckCircle2 className="h-3 w-3" />
                                <span>Settled</span>
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* Record Payment Modal */}
      {showPaymentModal && selectedInvoiceForPayment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl p-5">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3 mb-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Record Invoice Payment
              </h3>
              <button
                onClick={() => setShowPaymentModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <div className="mb-3 rounded-lg bg-slate-50 dark:bg-slate-950 p-3 border border-slate-200 dark:border-slate-800 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-500">Invoice:</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">{selectedInvoiceForPayment.invoice_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Total:</span>
                <span className="font-mono">{formatCurrency(selectedInvoiceForPayment.total_amount)}</span>
              </div>
              <div className="flex justify-between font-bold pt-1 border-t border-slate-200 dark:border-slate-800 text-amber-600 dark:text-amber-400">
                <span>Unpaid Left:</span>
                <span className="font-mono">{formatCurrency(selectedInvoiceForPayment.remaining_unpaid)}</span>
              </div>
            </div>

            <form onSubmit={handleRecordPayment} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Payment Amount (₹) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  max={selectedInvoiceForPayment.remaining_unpaid}
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-1.5 text-xs font-mono text-slate-900 dark:text-slate-100 focus:border-brand-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowPaymentModal(false)}
                  className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-1 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingPayment}
                  className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3.5 py-1 text-xs font-semibold text-white shadow-sm transition disabled:opacity-50"
                >
                  {submittingPayment ? "Recording..." : "Confirm Payment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
