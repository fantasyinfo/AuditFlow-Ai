import React, { useState } from "react";
import {
  FolderKanban,
  Plus,
  ArrowRight,
  AlertTriangle,
  FileText,
  DollarSign,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  Trash2,
  Sparkles,
  Building2,
  Percent,
} from "lucide-react";
import { api } from "../../api/client";
import { useProject } from "../../context/ProjectContext";

export function ProjectsModule({ onNavigate }) {
  const { projects, refreshProjects, selectProject, selectedProjectId } = useProject();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    name: "",
    code: "",
    description: "",
    vendor_name: "",
    vendor_gstin: "",
    budget_amount: "1000000.00",
    budget_currency: "INR",
    gst_rate_percent: "18.00",
    over_billing_tolerance_percent: "5.00",
    single_invoice_cap: "500000.00",
    start_date: "2026-01-01",
    end_date: "2026-12-31",
  });

  const handleCreateProject = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        name: formData.name.trim(),
        code: formData.code.trim(),
        description: formData.description?.trim() || null,
        vendor_name: formData.vendor_name.trim(),
        vendor_gstin: formData.vendor_gstin?.trim() || null,
        budget_amount: parseFloat(formData.budget_amount) || 0,
        budget_currency: formData.budget_currency || "INR",
        gst_rate_percent: parseFloat(formData.gst_rate_percent) || 0,
        over_billing_tolerance_percent: parseFloat(formData.over_billing_tolerance_percent) || 0,
        single_invoice_cap: formData.single_invoice_cap ? parseFloat(formData.single_invoice_cap) : null,
        start_date: formData.start_date || null,
        end_date: formData.end_date || null,
      };
      await api.projects.create(payload);
      await refreshProjects();
      setShowCreateModal(false);
      setFormData({
        name: "",
        code: "",
        description: "",
        vendor_name: "",
        vendor_gstin: "",
        budget_amount: "1000000.00",
        budget_currency: "INR",
        gst_rate_percent: "18.00",
        over_billing_tolerance_percent: "5.00",
        single_invoice_cap: "500000.00",
        start_date: "2026-01-01",
        end_date: "2026-12-31",
      });
    } catch (err) {
      setError(err.message || "Failed to create project");
    } finally {
      setSubmitting(false);
    }
  };

  const handleLoadDemoProject = async () => {
    setSubmitting(true);
    try {
      await api.projects.create({
        name: "TechNova ERP Cloud Migration",
        code: `PRJ-TECHNOVA-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
        description: "Enterprise multi-cloud migration and ERP software development contract.",
        vendor_name: "TechNova Solutions Ltd",
        vendor_gstin: "27AAACT2941Q1ZS",
        budget_amount: 1500000.00,
        budget_currency: "INR",
        gst_rate_percent: 18.00,
        over_billing_tolerance_percent: 5.00,
        single_invoice_cap: 500000.00,
      });
      await refreshProjects();
    } catch (err) {
      alert("Failed to load demo project: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete audit project '${name}'?`)) return;
    try {
      await api.projects.delete(id);
      await refreshProjects();
    } catch (err) {
      if (err.status === 404 || err.message?.toLowerCase().includes("not found")) {
        await refreshProjects();
      } else {
        alert("Failed to delete project: " + err.message);
      }
    }
  };

  const formatCurrency = (amt, currency = "INR") => {
    const val = parseFloat(amt) || 0;
    const symbol = currency === "INR" ? "₹" : "$";
    return `${symbol}${val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // Rollup totals
  const totalBudget = projects.reduce((acc, p) => acc + (parseFloat(p.budget_amount) || 0), 0);
  const totalInvoiced = projects.reduce((acc, p) => acc + (parseFloat(p.total_invoiced_gross) || 0), 0);
  const totalPaid = projects.reduce((acc, p) => acc + (parseFloat(p.total_paid_gross) || 0), 0);
  const overLoggedCount = projects.filter((p) => p.is_over_logged).length;

  return (
    <div className="space-y-6">
      {/* Calm Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <FolderKanban className="h-5 w-5 text-brand-600 dark:text-brand-400" />
            <span>Audit Projects & Quotation Baselines</span>
          </h1>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Track vendor quotation baselines, single invoice caps, and contract burn rates.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          {projects.length === 0 && (
            <button
              onClick={handleLoadDemoProject}
              disabled={submitting}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 px-3 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 transition shadow-sm"
            >
              <Sparkles className="h-3.5 w-3.5 text-brand-500" />
              <span>{submitting ? "Loading..." : "Load Demo Project"}</span>
            </button>
          )}

          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 px-3.5 py-2 text-xs font-semibold text-white shadow-sm transition"
          >
            <Plus className="h-4 w-4" />
            <span>New Project</span>
          </button>
        </div>
      </div>

      {/* When projects exist: KPI Cards */}
      {projects.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
              <span>Contracted Budget</span>
              <DollarSign className="h-4 w-4 text-brand-500" />
            </div>
            <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">{formatCurrency(totalBudget)}</p>
            <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">Across {projects.length} engagements</p>
          </div>

          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
              <span>Invoiced to Date</span>
              <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            </div>
            <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-100">{formatCurrency(totalInvoiced)}</p>
            <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">Total gross billed by vendors</p>
          </div>

          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
              <span>Disbursed (Paid)</span>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </div>
            <p className="mt-1 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{formatCurrency(totalPaid)}</p>
            <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">Remaining to pay: {formatCurrency(Math.max(0, totalBudget - totalPaid))}</p>
          </div>

          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-sm">
            <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
              <span>Over-Logged</span>
              <AlertTriangle className={`h-4 w-4 ${overLoggedCount > 0 ? "text-rose-500" : "text-emerald-500"}`} />
            </div>
            <p className={`mt-1 text-2xl font-bold ${overLoggedCount > 0 ? "text-rose-600 dark:text-rose-400" : "text-slate-900 dark:text-slate-100"}`}>
              {overLoggedCount}
            </p>
            <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
              {overLoggedCount > 0 ? "Exceeding agreed quotation baseline" : "All projects within agreed limits"}
            </p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {projects.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 p-10 text-center shadow-sm">
          <div className="w-12 h-12 rounded-xl bg-brand-50 dark:bg-brand-500/10 flex items-center justify-center text-brand-600 dark:text-brand-400 mx-auto mb-3">
            <FolderKanban className="h-6 w-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Start an Audit Project</h3>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto leading-relaxed">
            Create an engagement workspace with your vendor's quotation budget. AuditFlow will correlate all incoming invoices against the baseline to catch over-billing and calculate net payables.
          </p>

          <div className="mt-5 flex flex-wrap justify-center gap-2.5">
            <button
              onClick={handleLoadDemoProject}
              disabled={submitting}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 transition shadow-sm"
            >
              <Sparkles className="h-4 w-4 text-brand-500" />
              <span>{submitting ? "Loading..." : "Load TechNova ERP Demo"}</span>
            </button>

            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 px-4 py-2 text-xs font-semibold text-white shadow-sm transition"
            >
              <Plus className="h-4 w-4" />
              <span>Create Project</span>
            </button>
          </div>
        </div>
      ) : (
        /* Projects List */
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {projects.map((project) => {
            const budget = parseFloat(project.budget_amount) || 0;
            const invoiced = parseFloat(project.total_invoiced_gross) || 0;
            const paid = parseFloat(project.total_paid_gross) || 0;
            const burnRate = budget > 0 ? (invoiced / budget) * 100 : 0;
            const isOver = project.is_over_logged;
            const remainingToPay = Math.max(0, budget - paid);
            const isSelected = selectedProjectId === project.id;

            return (
              <div
                key={project.id}
                className={`rounded-xl border transition-all duration-150 p-5 flex flex-col justify-between ${
                  isSelected
                    ? "border-brand-500 dark:border-brand-500/80 bg-white dark:bg-slate-900 shadow-md ring-1 ring-brand-500/20"
                    : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/70 hover:border-slate-300 dark:hover:border-slate-700 shadow-sm"
                }`}
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                          {project.code}
                        </span>
                        {isOver ? (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-500/20">
                            +{project.variance_percent}% OVER-LOGGED
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/20">
                            WITHIN BUDGET
                          </span>
                        )}
                        {isSelected && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-brand-600 text-white">
                            Active Scope
                          </span>
                        )}
                      </div>

                      <h3 className="mt-2 text-base font-bold text-slate-900 dark:text-slate-100">
                        {project.name}
                      </h3>
                    </div>

                    <button
                      onClick={() => handleDelete(project.id, project.name)}
                      className="text-slate-400 hover:text-rose-500 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                      title="Delete Project"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Vendor Details */}
                  <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
                    <span className="flex items-center gap-1 font-medium text-slate-700 dark:text-slate-300">
                      <Building2 className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
                      {project.vendor_name}
                    </span>
                    {project.vendor_gstin && (
                      <span className="font-mono text-[11px]">
                        GSTIN: {project.vendor_gstin}
                      </span>
                    )}
                    <span>GST Rate: {project.gst_rate_percent}%</span>
                  </div>

                  {project.description && (
                    <p className="mt-2 text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                      {project.description}
                    </p>
                  )}

                  {/* Financial Grid */}
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 grid grid-cols-3 gap-2.5 text-xs">
                    <div className="rounded-lg bg-slate-50 dark:bg-slate-950 p-2 border border-slate-200 dark:border-slate-800/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Quoted Cap</span>
                      <span className="text-xs font-bold text-slate-800 dark:text-slate-200 mt-0.5 block">
                        {formatCurrency(budget, project.budget_currency)}
                      </span>
                    </div>

                    <div className="rounded-lg bg-slate-50 dark:bg-slate-950 p-2 border border-slate-200 dark:border-slate-800/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Invoiced</span>
                      <span className={`text-xs font-bold mt-0.5 block ${isOver ? "text-rose-600 dark:text-rose-400" : "text-slate-800 dark:text-slate-200"}`}>
                        {formatCurrency(invoiced, project.budget_currency)}
                      </span>
                    </div>

                    <div className="rounded-lg bg-slate-50 dark:bg-slate-950 p-2 border border-slate-200 dark:border-slate-800/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Remaining Left</span>
                      <span className="text-xs font-bold text-amber-600 dark:text-amber-400 mt-0.5 block">
                        {formatCurrency(remainingToPay, project.budget_currency)}
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <span className="text-slate-500 dark:text-slate-400">Budget Consumed</span>
                      <span className={`font-bold font-mono ${isOver ? "text-rose-600 dark:text-rose-400" : "text-slate-700 dark:text-slate-300"}`}>
                        {burnRate.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          isOver ? "bg-rose-500" : "bg-brand-600"
                        }`}
                        style={{ width: `${Math.min(100, burnRate)}%` }}
                      />
                    </div>
                  </div>

                  {/* Summary Footer */}
                  <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                    <span>
                      Paid: <strong className="text-slate-700 dark:text-slate-300">{formatCurrency(paid)}</strong>
                    </span>
                    <div className="flex items-center gap-2">
                      <span>{project.documents_count} docs</span>
                      <span>{project.invoices_count} invoices</span>
                      {project.open_findings_count > 0 && (
                        <span className="px-1.5 py-0.2 rounded bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400 font-bold border border-rose-200 dark:border-rose-500/20">
                          {project.open_findings_count} findings
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Card Action Footer */}
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
                  <button
                    onClick={() => {
                      selectProject(project.id);
                      if (onNavigate) onNavigate("reconciliation");
                    }}
                    className="inline-flex items-center gap-1 text-xs font-semibold text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 transition"
                  >
                    <span>Reconciliation & GST</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => {
                        selectProject(project.id);
                        if (onNavigate) onNavigate("documents");
                      }}
                      className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-medium transition"
                    >
                      + Add Files
                    </button>
                    <button
                      onClick={() => selectProject(project.id)}
                      className={`px-3 py-1 rounded text-xs font-semibold transition ${
                        isSelected
                          ? "bg-brand-600 text-white"
                          : "bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
                      }`}
                    >
                      {isSelected ? "Active" : "Select"}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Clean Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="relative w-full max-w-xl rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl p-5 my-8">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3 mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  New Audit Project Workspace
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Set baseline quotation budget, GST rate, and single invoice caps.
                </p>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            {error && (
              <div className="mb-4 rounded-lg bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/20 p-2.5 text-xs text-rose-600 dark:text-rose-400">
                {error}
              </div>
            )}

            <form onSubmit={handleCreateProject} className="space-y-3.5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Project Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. ERP Cloud Migration"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-brand-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Code *</label>
                  <input
                    type="text"
                    required
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                    placeholder="e.g. PRJ-TECHNOVA-01"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-1.5 text-xs font-mono text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-brand-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Vendor Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.vendor_name}
                    onChange={(e) => setFormData({ ...formData, vendor_name: e.target.value })}
                    placeholder="e.g. TechNova Solutions Ltd"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-brand-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Vendor GSTIN (Optional)</label>
                  <input
                    type="text"
                    value={formData.vendor_gstin}
                    onChange={(e) => setFormData({ ...formData, vendor_gstin: e.target.value.toUpperCase() })}
                    placeholder="e.g. 27AAACT2941Q1ZS"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-1.5 text-xs font-mono text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-brand-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Financial Parameters */}
              <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Quoted Budget (₹) *</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={formData.budget_amount}
                      onChange={(e) => setFormData({ ...formData, budget_amount: e.target.value })}
                      placeholder="1000000.00"
                      className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs font-mono text-slate-900 dark:text-slate-100 focus:border-brand-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">GST Rate %</label>
                    <input
                      type="number"
                      step="0.1"
                      required
                      value={formData.gst_rate_percent}
                      onChange={(e) => setFormData({ ...formData, gst_rate_percent: e.target.value })}
                      placeholder="18.0"
                      className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs font-mono text-slate-900 dark:text-slate-100 focus:border-brand-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">Over-Billing Tol. %</label>
                    <input
                      type="number"
                      step="0.1"
                      required
                      value={formData.over_billing_tolerance_percent}
                      onChange={(e) => setFormData({ ...formData, over_billing_tolerance_percent: e.target.value })}
                      placeholder="5.0"
                      className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs font-mono text-slate-900 dark:text-slate-100 focus:border-brand-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Single Invoice Cap (₹, Optional)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.single_invoice_cap}
                    onChange={(e) => setFormData({ ...formData, single_invoice_cap: e.target.value })}
                    placeholder="e.g. 500000.00"
                    className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs font-mono text-slate-900 dark:text-slate-100 focus:border-brand-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Scope Notes</label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Summary of deliverables, milestone terms, or legal clauses..."
                  className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-1.5 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-brand-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-slate-300 dark:border-slate-700 px-3.5 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-lg bg-brand-600 hover:bg-brand-500 px-4 py-1.5 text-xs font-semibold text-white shadow transition disabled:opacity-50"
                >
                  {submitting ? "Creating..." : "Create Project"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
