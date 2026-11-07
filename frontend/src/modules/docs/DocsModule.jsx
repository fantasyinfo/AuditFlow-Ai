import React, { useState } from "react";
import {
  BookOpen,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Receipt,
  Bot,
  History,
  Building,
  ArrowRight,
  Layers,
  Search,
  Lock,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

export default function DocsModule({ onNavigate }) {
  const [activeTab, setActiveTab] = useState("overview"); // overview | step-by-step | modules | rules

  const steps = [
    {
      num: "01",
      title: "Ingest Commercial Documents",
      desc: "Upload invoices, quotations, contracts, or purchase orders in PDF or CSV format. Any global layout, template, or currency ($ USD, € EUR, £ GBP, ₹ INR) is supported.",
      actionText: "Go to Ingestion",
      targetModule: "documents",
      icon: FileText,
      color: "from-brand-600 to-indigo-600",
    },
    {
      num: "02",
      title: "Automated Rules & Anomaly Detection",
      desc: "Background Celery workers extract fields via Gemini and immediately evaluate 5 deterministic audit rules (Duplicates, Mismatches, Missing POs, Tax IDs, Spikes).",
      actionText: "Review Findings",
      targetModule: "findings",
      icon: AlertTriangle,
      color: "from-amber-600 to-orange-600",
    },
    {
      num: "03",
      title: "Investigate with AI Audit Assistant",
      desc: "Ask plain-English audit questions. The agent searches pgvector document chunks, checks findings, and answers with mandatory verifiable citations.",
      actionText: "Open AI Assistant",
      targetModule: "assistant",
      icon: Bot,
      color: "from-purple-600 to-pink-600",
    },
  ];

  const modulesInfo = [
    {
      id: "dashboard",
      name: "Dashboard",
      icon: ShieldCheck,
      badge: "Command Center",
      summary: "Real-time visibility into organization-wide accounts payable health.",
      whatItDoes:
        "Displays aggregated KPIs: Total Ingested Documents, Open Audit Findings, Total Financial Amount at Risk (sum of flagged invoices), and Recent High-Priority Alerts.",
      howToUse:
        "Check this screen daily to spot high-severity alerts before releasing invoice payments to vendors.",
    },
    {
      id: "documents",
      name: "Document Ingestion",
      icon: FileText,
      badge: "Redis + pgvector",
      summary: "Universal drag-and-drop file ingestion and asynchronous queueing.",
      whatItDoes:
        "Accepts commercial PDFs and CSVs, returns an instant 202 Accepted, and processes files in the background via Celery. Splits text into chunks with page numbers and computes 1536-dimensional vector embeddings.",
      howToUse:
        "Select your file, choose its category (Invoice, Quote, Agreement, PO), and click 'Upload & Enqueue'. Use 'Inspect Chunks' to view vector embeddings.",
    },
    {
      id: "invoices",
      name: "Commercial Records",
      icon: Receipt,
      badge: "Gemini Extraction",
      summary: "Structured financial catalog extracted from non-fixed layouts.",
      whatItDoes:
        "Uses Google AI Studio (Gemini) to dynamically detect vendor names, invoice numbers, dates, amounts, taxes, and PO links without rigid regex or fixed templates.",
      howToUse:
        "Search by vendor or invoice number. Click on any invoice row to open the Detail Drawer and inspect associated audit findings.",
    },
    {
      id: "findings",
      name: "Audit Findings",
      icon: AlertTriangle,
      badge: "5 Detection Rules",
      summary: "Central hub for reviewing flagged anomalies and fraud risks.",
      whatItDoes:
        "Lists violations flagged by the deterministic rules engine. Each finding carries severity (Critical, High, Medium), affected invoice, and exact detection reason.",
      howToUse:
        "Auditors review open findings and click 'Confirm' or 'Dismiss', providing an explanation that is committed to the immutable audit trail.",
    },
    {
      id: "assistant",
      name: "AI Audit Assistant",
      icon: Bot,
      badge: "Gemini + RAG",
      summary: "Natural-language audit investigator with mandatory citations.",
      whatItDoes:
        "LangChain agent that queries vector chunks and findings. Strictly read-only: cannot mutate data. Mandatory citations: outputs [filename.pdf p.X] and [finding #ID]. Refuses ungrounded facts with 'I could not find this in your documents.'",
      howToUse:
        "Click the pre-built prompt pills or type questions like 'Are there duplicate invoices?' or 'Does the invoice price match Quotation #Q-901?'.",
    },
    {
      id: "audit-logs",
      name: "Immutable Audit Trail",
      icon: History,
      badge: "Compliance Trail",
      summary: "Append-only operational history for non-repudiation and compliance.",
      whatItDoes:
        "Records every sensitive event: finding confirmed/dismissed, document uploaded, user actions, timestamps, and side-by-side before/after JSON diffs.",
      howToUse:
        "Click 'Inspect Diff' on any log entry to verify exact before and after states for accounting and regulatory audits.",
    },
  ];

  const rulesInfo = [
    {
      name: "Duplicate Invoice Detection",
      code: "duplicate_invoice",
      severity: "Critical",
      catches:
        "Flags invoices submitted with identical vendor + invoice number, or matching vendor + amount + date.",
      whyItMatters: "Prevents double-paying vendors for the exact same delivery.",
    },
    {
      name: "PO Amount Mismatch",
      code: "amount_mismatch",
      severity: "High",
      catches:
        "Compares the invoice total against the linked Purchase Order total and flags differences exceeding ₹1.00 tolerance.",
      whyItMatters: "Catches vendor overbilling and unauthorized price escalations.",
    },
    {
      name: "Missing Evidence / No PO",
      code: "missing_evidence",
      severity: "Medium",
      catches:
        "Identifies commercial invoices exceeding ₹10,000 / $1,000 that lack a linked PO or approved contract.",
      whyItMatters: "Ensures company purchase authorization policies are strictly enforced.",
    },
    {
      name: "GSTIN / Tax ID Format Check",
      code: "invalid_gstin",
      severity: "High",
      catches:
        "Validates vendor tax numbers (e.g. Indian 15-character GSTIN, European VAT, US EIN) against statutory checksum regexes.",
      whyItMatters: "Eliminates tax credit disallowances and non-compliant shell suppliers.",
    },
    {
      name: "Unusual Amount Spike",
      code: "unusual_amount",
      severity: "Medium",
      catches:
        "Flags invoices whose amount is more than 2.5× the vendor's historical average billing.",
      whyItMatters: "Detects fraudulent invoices with artificially inflated figures.",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-6 md:p-8 rounded-2xl bg-gradient-to-r from-brand-900/40 via-purple-900/20 to-slate-900/60 dark:from-brand-950/70 dark:via-purple-950/40 dark:to-slate-900 border border-brand-500/20 shadow-xl space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-brand-500/20 text-brand-400 dark:text-brand-300 border border-brand-500/30 flex items-center gap-1.5">
            <BookOpen className="w-3.5 h-3.5" />
            <span>AuditFlow User Guide & Manual</span>
          </span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          How AuditFlow AI Protects Your Organization
        </h1>
        <p className="text-xs md:text-sm text-slate-600 dark:text-slate-300 max-w-2xl leading-relaxed">
          AuditFlow AI is an automated Accounts Payable audit platform. It ingests commercial invoices, quotations, contracts, and purchase orders in arbitrary global formats, identifies billing anomalies deterministically, and provides a citation-backed AI assistant powered by Google AI Studio (Gemini).
        </p>

        {/* Tab Buttons */}
        <div className="pt-2 flex flex-wrap gap-2">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "overview"
                ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                : "bg-white/80 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-brand-500"
            }`}
          >
            Overview & 3-Step Guide
          </button>
          <button
            onClick={() => setActiveTab("modules")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "modules"
                ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                : "bg-white/80 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-brand-500"
            }`}
          >
            Module-by-Module Guide
          </button>
          <button
            onClick={() => setActiveTab("rules")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === "rules"
                ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                : "bg-white/80 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-brand-500"
            }`}
          >
            Detection Rules Explained
          </button>
        </div>
      </div>

      {/* Tab 1: Overview & Step-by-Step */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* 3-Step Process Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {steps.map((s, idx) => {
              const Icon = s.icon;
              return (
                <div
                  key={idx}
                  className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 flex flex-col justify-between space-y-4 shadow-sm hover:shadow-md transition"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xl font-mono font-bold text-brand-600 dark:text-brand-400">
                        {s.num}
                      </span>
                      <div className="w-8 h-8 rounded-lg bg-brand-500/10 dark:bg-brand-500/20 text-brand-600 dark:text-brand-300 flex items-center justify-center">
                        <Icon className="w-4 h-4" />
                      </div>
                    </div>
                    <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                      {s.title}
                    </h3>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                      {s.desc}
                    </p>
                  </div>

                  <button
                    onClick={() => onNavigate(s.targetModule)}
                    className="pt-2 text-xs font-semibold text-brand-600 dark:text-brand-400 hover:text-brand-500 flex items-center gap-1 group transition"
                  >
                    <span>{s.actionText}</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </button>
                </div>
              );
            })}
          </div>

          {/* Key Value Pillars */}
          <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 space-y-4">
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-brand-500" />
              <span>Core Architectural Safeguards</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="font-semibold text-slate-900 dark:text-slate-200 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Strict Multi-Tenancy
                </span>
                <p className="text-slate-600 dark:text-slate-400 text-[11px]">
                  Every database table and query is isolated by tenant_id. Tenant B can never view or search Tenant A's documents.
                </p>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="font-semibold text-slate-900 dark:text-slate-200 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Financial Precision
                </span>
                <p className="text-slate-600 dark:text-slate-400 text-[11px]">
                  All money values are stored as NUMERIC(18,2) in PostgreSQL and Decimal in Python. Zero floating-point drift.
                </p>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="font-semibold text-slate-900 dark:text-slate-200 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Read-Only AI Agent
                </span>
                <p className="text-slate-600 dark:text-slate-400 text-[11px]">
                  The assistant cannot delete or modify records. Any mutation attempt triggers an immediate safety refusal.
                </p>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="font-semibold text-slate-900 dark:text-slate-200 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  Mandatory Citations
                </span>
                <p className="text-slate-600 dark:text-slate-400 text-[11px]">
                  Every claim links to source document chunks [file.pdf p.X] or finding records [finding #ID].
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Module-by-Module Guide */}
      {activeTab === "modules" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {modulesInfo.map((m) => {
            const Icon = m.icon;
            return (
              <div
                key={m.id}
                className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 space-y-3 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-brand-500/10 dark:bg-brand-500/20 text-brand-600 dark:text-brand-400 flex items-center justify-center">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                        {m.name}
                      </h3>
                      <p className="text-[11px] text-slate-500">{m.summary}</p>
                    </div>
                  </div>
                  <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                    {m.badge}
                  </span>
                </div>

                <div className="space-y-2 text-xs pt-1">
                  <div>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      What it does:{" "}
                    </span>
                    <span className="text-slate-600 dark:text-slate-400">{m.whatItDoes}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-brand-600 dark:text-brand-400">
                      How to use:{" "}
                    </span>
                    <span className="text-slate-600 dark:text-slate-400">{m.howToUse}</span>
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={() => onNavigate(m.id)}
                    className="text-[11px] font-semibold text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
                  >
                    <span>Open {m.name}</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Tab 3: Detection Rules Explained */}
      {activeTab === "rules" && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400">
            AuditFlow AI uses deterministic Python detection rules that run synchronously in Celery workers right after document parsing. They evaluate mathematical and compliance invariants without hallucinating.
          </div>

          <div className="grid grid-cols-1 gap-3">
            {rulesInfo.map((r, idx) => (
              <div
                key={idx}
                className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 space-y-2 text-xs shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                      {r.name}
                    </span>
                    <span className="font-mono text-[10px] text-brand-600 dark:text-brand-400 bg-brand-500/10 px-1.5 py-0.5 rounded">
                      {r.code}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                      r.severity === "Critical"
                        ? "bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/30"
                        : r.severity === "High"
                        ? "bg-orange-500/20 text-orange-600 dark:text-orange-400 border border-orange-500/30"
                        : "bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30"
                    }`}
                  >
                    {r.severity} Severity
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-600 dark:text-slate-400 pt-1">
                  <div>
                    <strong className="text-slate-800 dark:text-slate-300">Criteria: </strong>
                    {r.catches}
                  </div>
                  <div>
                    <strong className="text-emerald-600 dark:text-emerald-400">Why it matters: </strong>
                    {r.whyItMatters}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
