import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  Plus,
  Trash2,
  ToggleLeft,
  ToggleRight,
  Sparkles,
  HelpCircle,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  BookOpen,
  Filter,
  RefreshCw,
  X,
  ArrowRight,
  Info,
  Sliders,
} from "lucide-react";
import { api } from "../../api/client";

const RULE_PRESETS = [
  {
    title: "Executive Approval Threshold (> ₹2,00,000)",
    desc: "Flags any invoice exceeding ₹2,00,000 for Chief Procurement Officer approval.",
    preset: {
      name: "Executive Approval Threshold",
      code: "cpo_approval_limit",
      severity: "high",
      rule_type: "amount_threshold",
      field_to_evaluate: "total_amount",
      operator: ">",
      threshold_value: "200000.00",
      reason_template: "High-value invoice for {amount} from {vendor} exceeds ₹{threshold} limit and requires CPO authorization.",
    },
  },
  {
    title: "Weekend Billing Anomaly (Sat/Sun Invoice)",
    desc: "Detects invoices dated on weekends when offices are closed.",
    preset: {
      name: "Weekend Invoicing Anomaly",
      code: "weekend_billing_flag",
      severity: "medium",
      rule_type: "date_check",
      field_to_evaluate: "invoice_date",
      operator: "weekend",
      threshold_value: "weekend",
      reason_template: "Invoice {invoice_number} from {vendor} was issued on a weekend ({weekday}), indicating potential backdating.",
    },
  },
  {
    title: "Strict Mandatory Tax ID (Missing GSTIN)",
    desc: "Flags any invoice where supplier tax ID (GSTIN) is blank or missing.",
    preset: {
      name: "Strict Mandatory GSTIN",
      code: "missing_vendor_gstin",
      severity: "high",
      rule_type: "missing_field",
      field_to_evaluate: "vendor_gstin",
      operator: "is_empty",
      threshold_value: "mandatory",
      reason_template: "Invoice {invoice_number} from {vendor} is missing statutory tax identification (GSTIN).",
    },
  },
  {
    title: "High-Risk Keyword Scanner (Rush/Cash)",
    desc: "Scans document text for suspicious terms like 'rush fee' or 'confidential'.",
    preset: {
      name: "Suspicious Fee Keyword Scanner",
      code: "high_risk_keywords",
      severity: "critical",
      rule_type: "keyword_check",
      field_to_evaluate: "text_content",
      operator: "contains",
      threshold_value: "rush fee",
      reason_template: "Document contains prohibited payment keyword '{threshold}' requiring fraud officer review.",
    },
  },
];

export default function RulesModule() {
  const [rules, setRules] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all"); // "all" | "custom" | "guide"
  const [severityFilter, setSeverityFilter] = useState("");

  // Create Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    severity: "high",
    rule_type: "amount_threshold",
    field_to_evaluate: "total_amount",
    operator: ">",
    threshold_value: "",
    reason_template: "Invoice from {vendor} violates custom policy: {name} (Threshold: {threshold}).",
    is_active: true,
  });

  const fetchRules = async () => {
    setIsLoading(true);
    try {
      const data = await api.rules.list();
      setRules(data);
    } catch (err) {
      console.error("Failed to load rules:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleApplyPreset = (p) => {
    setFormData({
      ...p.preset,
      code: `${p.preset.code}_${Math.random().toString(36).substring(2, 6)}`,
      is_active: true,
    });
    setFormError(null);
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);
    try {
      await api.rules.createCustom(formData);
      setShowCreateModal(false);
      fetchRules();
    } catch (err) {
      setFormError(err.message || "Failed to create rule");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleRule = async (rule) => {
    if (!rule.custom_rule_id) return;
    try {
      await api.rules.updateCustom(rule.custom_rule_id, {
        is_active: !rule.is_active,
      });
      fetchRules();
    } catch (err) {
      alert("Failed to toggle rule: " + err.message);
    }
  };

  const handleDeleteRule = async (rule) => {
    if (!rule.custom_rule_id) return;
    if (!confirm(`Are you sure you want to delete custom rule "${rule.name}"?`)) return;
    try {
      await api.rules.deleteCustom(rule.custom_rule_id);
      fetchRules();
    } catch (err) {
      alert("Failed to delete rule: " + err.message);
    }
  };

  const filteredRules = rules.filter((r) => {
    if (activeTab === "custom" && !r.is_custom) return false;
    if (severityFilter && r.severity !== severityFilter) return false;
    return true;
  });

  const customCount = rules.filter((r) => r.is_custom).length;
  const builtinCount = rules.filter((r) => !r.is_custom).length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-6 md:p-8 rounded-2xl bg-gradient-to-r from-brand-900/60 via-purple-900/40 to-slate-900 border border-brand-500/20 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-brand-500/20 text-brand-300 border border-brand-500/30 flex items-center gap-1.5 w-fit">
              <Sliders className="w-3.5 h-3.5 text-brand-400" />
              <span>Deterministic Audit Rules Engine</span>
            </span>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white">
              Audit Rules & Tenant Policy Builder
            </h1>
            <p className="text-xs md:text-sm text-slate-300 max-w-2xl">
              AuditFlow evaluates deterministic rules in background Celery workers on every document. Create custom threshold and compliance rules tailored to your organization.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setShowCreateModal(true);
                setFormError(null);
              }}
              className="px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold transition flex items-center gap-2 shadow-lg shadow-brand-600/30 shrink-0"
            >
              <Plus className="w-4 h-4" />
              <span>Create Custom Rule</span>
            </button>
          </div>
        </div>

        {/* Tab & Filter Controls */}
        <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-slate-800">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === "all"
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-slate-800/80 text-slate-300 hover:text-white"
              }`}
            >
              All Rules ({rules.length})
            </button>
            <button
              onClick={() => setActiveTab("custom")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === "custom"
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-slate-800/80 text-slate-300 hover:text-white"
              }`}
            >
              Custom Policies ({customCount})
            </button>
            <button
              onClick={() => setActiveTab("guide")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 ${
                activeTab === "guide"
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-slate-800/80 text-slate-300 hover:text-white"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Step-by-Step Guide</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg py-1.5 px-3 text-xs text-slate-300 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <button
              onClick={fetchRules}
              className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition"
              title="Refresh Catalog"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* View 1 & 2: Rules Catalog */}
      {activeTab !== "guide" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredRules.map((rule, idx) => {
            const isCustom = rule.is_custom;
            return (
              <div
                key={rule.code || idx}
                className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 space-y-3 shadow-sm hover:shadow-md transition flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                        {rule.name}
                      </span>
                      {isCustom ? (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-700 dark:text-purple-300 border border-purple-500/20 font-semibold">
                          Custom
                        </span>
                      ) : (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                          Built-in
                        </span>
                      )}
                    </div>

                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                        rule.severity === "critical"
                          ? "bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20"
                          : rule.severity === "high"
                          ? "bg-orange-500/10 text-orange-700 dark:text-orange-300 border border-orange-500/20"
                          : "bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20"
                      }`}
                    >
                      {rule.severity}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    {rule.description}
                  </p>

                  <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/80 font-mono text-[11px] text-slate-600 dark:text-slate-300 space-y-1">
                    <div>
                      <span className="text-slate-400">Code: </span>
                      <span className="text-brand-600 dark:text-brand-400 font-semibold">{rule.code}</span>
                    </div>
                    {rule.reason_template && (
                      <div className="truncate">
                        <span className="text-slate-400">Template: </span>
                        <span className="text-slate-500 dark:text-slate-400">{rule.reason_template}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        rule.is_active ? "bg-emerald-500" : "bg-slate-400"
                      }`}
                    />
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">
                      {rule.is_active ? "Active in Pipeline" : "Deactivated"}
                    </span>
                  </div>

                  {isCustom && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggleRule(rule)}
                        className="px-2 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded text-[11px] font-medium transition"
                      >
                        {rule.is_active ? "Deactivate" : "Activate"}
                      </button>
                      <button
                        onClick={() => handleDeleteRule(rule)}
                        className="p-1 text-slate-400 hover:text-rose-500 transition"
                        title="Delete Rule"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* View 3: Step-by-Step Guide & Tutorial */}
      {activeTab === "guide" && (
        <div className="space-y-6">
          <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 space-y-4 shadow-sm">
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-brand-600 dark:text-brand-400" />
              <span>Step-by-Step Guide: How to Create Your Own Audit Rules</span>
            </h2>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Every organization has unique procurement policies, spending thresholds, and compliance requirements. AuditFlow AI allows finance admins to define condition-based custom rules evaluated synchronously on every commercial invoice during background ingestion.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2">
                <span className="text-xs font-mono font-bold text-brand-600 dark:text-brand-400">
                  STEP 01
                </span>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Select Rule Type & Target Field
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Choose what aspect to evaluate: monetary amount, specific vendor name, missing fields (like GSTIN), weekend billing date, or suspicious text keywords.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2">
                <span className="text-xs font-mono font-bold text-brand-600 dark:text-brand-400">
                  STEP 02
                </span>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Define Operator & Threshold Value
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Set mathematical comparison operators (e.g. &gt;, &gt;=, &lt;=) or string filters (contains, is_empty). Enter the threshold operand (e.g. 50000.00).
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2">
                <span className="text-xs font-mono font-bold text-brand-600 dark:text-brand-400">
                  STEP 03
                </span>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Formulate Dynamic Reason Template
                </h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Provide an explanation template with dynamic variables like <code className="text-brand-500">{"{vendor}"}</code>, <code className="text-brand-500">{"{amount}"}</code>, and <code className="text-brand-500">{"{threshold}"}</code>.
                </p>
              </div>
            </div>
          </div>

          {/* Supported Fields Reference Table */}
          <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 space-y-4 shadow-sm">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <FileCode className="w-4 h-4 text-brand-600 dark:text-brand-400" />
              <span>Available Rule Fields & Operator Reference</span>
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
                <thead className="bg-slate-50 dark:bg-slate-950/70 uppercase text-[10px] text-slate-500 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Rule Type</th>
                    <th className="py-2.5 px-3">Target Field</th>
                    <th className="py-2.5 px-3">Supported Operators</th>
                    <th className="py-2.5 px-3">Threshold Example</th>
                    <th className="py-2.5 px-3">Practical Business Purpose</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  <tr>
                    <td className="py-2.5 px-3 font-mono font-semibold text-brand-600 dark:text-brand-400">amount_threshold</td>
                    <td className="py-2.5 px-3 font-mono">total_amount</td>
                    <td className="py-2.5 px-3 font-mono">&gt;, &gt;=, &lt;, &lt;=, ==</td>
                    <td className="py-2.5 px-3 font-mono">200000.00</td>
                    <td className="py-2.5 px-3">Flag invoices requiring senior management approval</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-mono font-semibold text-brand-600 dark:text-brand-400">vendor_match</td>
                    <td className="py-2.5 px-3 font-mono">vendor_name</td>
                    <td className="py-2.5 px-3 font-mono">contains, ==, starts_with</td>
                    <td className="py-2.5 px-3 font-mono">Consulting</td>
                    <td className="py-2.5 px-3">Scrutinize high-risk vendors or restricted supplier categories</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-mono font-semibold text-brand-600 dark:text-brand-400">missing_field</td>
                    <td className="py-2.5 px-3 font-mono">vendor_gstin, po_number</td>
                    <td className="py-2.5 px-3 font-mono">is_empty</td>
                    <td className="py-2.5 px-3 font-mono">mandatory</td>
                    <td className="py-2.5 px-3">Enforce statutory tax ID and approved PO reference on all bills</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-mono font-semibold text-brand-600 dark:text-brand-400">date_check</td>
                    <td className="py-2.5 px-3 font-mono">invoice_date</td>
                    <td className="py-2.5 px-3 font-mono">weekend, future</td>
                    <td className="py-2.5 px-3 font-mono">weekend</td>
                    <td className="py-2.5 px-3">Detect invoices dated on Saturday/Sunday or in the future</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-mono font-semibold text-brand-600 dark:text-brand-400">keyword_check</td>
                    <td className="py-2.5 px-3 font-mono">text_content</td>
                    <td className="py-2.5 px-3 font-mono">contains</td>
                    <td className="py-2.5 px-3 font-mono">rush fee</td>
                    <td className="py-2.5 px-3">Scan document text for unauthorized surcharges or bribery terms</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Create Custom Rule */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-2xl p-6 space-y-5 shadow-2xl my-8">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Plus className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Create Custom Audit Rule
                </h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* 1-Click Quick Presets */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-500" />
                <span>Quick-Start Presets (1-Click Fill)</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {RULE_PRESETS.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleApplyPreset(p)}
                    className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 hover:border-brand-500 text-left transition space-y-0.5 group"
                  >
                    <div className="text-[11px] font-bold text-slate-900 dark:text-slate-200 group-hover:text-brand-600 dark:group-hover:text-brand-400">
                      {p.title}
                    </div>
                    <div className="text-[10px] text-slate-500 truncate">{p.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {formError && (
              <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Rule Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Director Approval Required"
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Rule Identifier Code *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.code}
                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "_") })}
                    placeholder="e.g. director_approval_limit"
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-xs text-slate-900 dark:text-slate-200 font-mono focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Rule Type
                  </label>
                  <select
                    value={formData.rule_type}
                    onChange={(e) => {
                      const type = e.target.value;
                      let field = "total_amount";
                      let op = ">";
                      let defVal = "100000.00";
                      if (type === "vendor_match") { field = "vendor_name"; op = "contains"; defVal = "Consulting"; }
                      if (type === "missing_field") { field = "vendor_gstin"; op = "is_empty"; defVal = "mandatory"; }
                      if (type === "date_check") { field = "invoice_date"; op = "weekend"; defVal = "weekend"; }
                      if (type === "keyword_check") { field = "text_content"; op = "contains"; defVal = "rush fee"; }
                      setFormData({ ...formData, rule_type: type, field_to_evaluate: field, operator: op, threshold_value: defVal });
                    }}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-brand-500"
                  >
                    <option value="amount_threshold">Amount Threshold</option>
                    <option value="vendor_match">Vendor Name Check</option>
                    <option value="missing_field">Missing Field / Invariant</option>
                    <option value="date_check">Date & Weekend Anomaly</option>
                    <option value="keyword_check">Document Keyword Scan</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Operator
                  </label>
                  <select
                    value={formData.operator}
                    onChange={(e) => setFormData({ ...formData, operator: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-brand-500"
                  >
                    <option value=">">Greater than (&gt;)</option>
                    <option value=">=">Greater or equal (&gt;=)</option>
                    <option value="<">Less than (&lt;)</option>
                    <option value="<=">Less or equal (&lt;=)</option>
                    <option value="==">Exact Match (==)</option>
                    <option value="contains">Contains Substring</option>
                    <option value="is_empty">Is Empty / Missing</option>
                    <option value="weekend">Is Weekend (Sat/Sun)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                    Severity
                  </label>
                  <select
                    value={formData.severity}
                    onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-brand-500"
                  >
                    <option value="critical">Critical (Payment Hold)</option>
                    <option value="high">High (Auditor Review)</option>
                    <option value="medium">Medium (Warning)</option>
                    <option value="low">Low (Informational)</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Threshold Value *
                </label>
                <input
                  type="text"
                  required
                  value={formData.threshold_value}
                  onChange={(e) => setFormData({ ...formData, threshold_value: e.target.value })}
                  placeholder="e.g. 200000.00 or Consulting"
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-xs text-slate-900 dark:text-slate-200 font-mono focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Reason Explanation Template *
                </label>
                <textarea
                  rows={2}
                  required
                  value={formData.reason_template}
                  onChange={(e) => setFormData({ ...formData, reason_template: e.target.value })}
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg p-2 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-brand-500"
                />
                <p className="text-[10px] text-slate-500">
                  Tokens available: <code className="text-brand-500">{"{vendor}"}</code>, <code className="text-brand-500">{"{amount}"}</code>, <code className="text-brand-500">{"{threshold}"}</code>, <code className="text-brand-500">{"{name}"}</code>
                </p>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition shadow-md shadow-brand-600/30"
                >
                  {isSubmitting ? "Creating Rule..." : "Create & Activate Rule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
