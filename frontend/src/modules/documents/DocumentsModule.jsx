import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Database,
  Layers,
  Key,
  RefreshCw,
  X,
  FileCode,
  Sparkles,
  Eye,
  ArrowRight,
  BookOpen,
  Receipt,
  FileCheck,
  FolderKanban,
  Trash2,
  Cpu,
  Info,
  ExternalLink,
  ShieldCheck,
  AlertTriangle,
} from "lucide-react";
import { api } from "../../api/client";
import { DEMO_DOCUMENTS } from "../../data/demoDocuments";
import { useProject } from "../../context/ProjectContext";
import ConfirmModal from "../../components/common/ConfirmModal";

export default function DocumentsModule({ onNavigate }) {
  const { projects, selectedProjectId } = useProject();
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);
  const [docType, setDocType] = useState("invoice");
  const [targetProjectId, setTargetProjectId] = useState(selectedProjectId || "");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null);

  // AI Engine Status & Configuration
  const [aiStatus, setAiStatus] = useState(null);
  const [showAiConfigModal, setShowAiConfigModal] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [isConfiguringAi, setIsConfiguringAi] = useState(false);
  const [aiConfigMessage, setAiConfigMessage] = useState(null);

  // Diagnostics & Extraction Details Modal
  const [diagnosticsDoc, setDiagnosticsDoc] = useState(null);
  const [docInvoices, setDocInvoices] = useState([]);
  const [isLoadingDocInvoices, setIsLoadingDocInvoices] = useState(false);

  useEffect(() => {
    if (selectedProjectId) {
      setTargetProjectId(selectedProjectId);
    }
  }, [selectedProjectId]);

  // Demo Document Library & Preview State
  const [showDemoLibrary, setShowDemoLibrary] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);

  // Chunks Inspector Modal State
  const [inspectDoc, setInspectDoc] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [isLoadingChunks, setIsLoadingChunks] = useState(false);

  const fetchDocuments = async () => {
    try {
      const data = await api.documents.list("", 50);
      setDocuments(data);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAiStatus = async () => {
    try {
      const status = await api.system.getAiStatus();
      setAiStatus(status);
    } catch (err) {
      console.warn("Could not fetch AI engine status:", err);
    }
  };

  useEffect(() => {
    fetchDocuments();
    fetchAiStatus();
    const interval = setInterval(fetchDocuments, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleOpenDiagnostics = async (doc) => {
    setDiagnosticsDoc(doc);
    setIsLoadingDocInvoices(true);
    try {
      const invs = await api.invoices.list(50, doc.id);
      setDocInvoices(invs || []);
    } catch (err) {
      console.error("Failed to load invoices for diagnostics:", err);
      setDocInvoices([]);
    } finally {
      setIsLoadingDocInvoices(false);
    }
  };

  const handleConfigureAi = async (e) => {
    e.preventDefault();
    if (!apiKeyInput.trim()) return;
    setIsConfiguringAi(true);
    setAiConfigMessage(null);
    try {
      const res = await api.system.configureAi(apiKeyInput.trim());
      setAiConfigMessage({ type: "success", text: res.message });
      setApiKeyInput("");
      await fetchAiStatus();
      setTimeout(() => {
        setShowAiConfigModal(false);
        setAiConfigMessage(null);
      }, 2000);
    } catch (err) {
      setAiConfigMessage({
        type: "error",
        text: err.message || "Failed to configure Google AI Studio API key.",
      });
    } finally {
      setIsConfiguringAi(false);
    }
  };

  const generateKey = () => {
    const key = "idemp_" + Math.random().toString(36).substring(2, 12);
    setIdempotencyKey(key);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadMessage(null);

    try {
      const res = await api.documents.upload(selectedFile, docType, idempotencyKey, targetProjectId);
      setUploadMessage({
        type: "success",
        text: `Uploaded "${res.filename}" (ID: ${res.id}). Queued in Redis for parsing & embeddings!`,
      });
      setSelectedFile(null);
      fetchDocuments();
    } catch (err) {
      setUploadMessage({
        type: "error",
        text: err.message || "Failed to upload document",
      });
    } finally {
      setIsUploading(false);
    }
  };

  // Delete confirmation modal state
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteClick = (doc) => {
    setDeleteTarget({ id: doc.id, name: doc.filename });
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await api.documents.delete(deleteTarget.id);
      setDeleteTarget(null);
      await fetchDocuments();
    } catch (err) {
      alert("Failed to delete document: " + err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleIngestDemoDoc = async (demo) => {
    setIsUploading(true);
    setUploadMessage(null);
    try {
      const blob = new Blob([demo.rawContent], { type: "text/csv" });
      const file = new File([blob], demo.filename, { type: "text/csv" });
      const res = await api.documents.upload(file, demo.type, `idemp_demo_${Date.now()}`, targetProjectId);
      setUploadMessage({
        type: "success",
        text: `Ingested demo document "${demo.title}" (${res.id}). Celery worker is processing rules!`,
      });
      setShowDemoLibrary(false);
      setPreviewDoc(null);
      fetchDocuments();
    } catch (err) {
      setUploadMessage({
        type: "error",
        text: err.message || "Failed to ingest demo document",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const openChunksModal = async (doc) => {
    setInspectDoc(doc);
    setIsLoadingChunks(true);
    try {
      const data = await api.documents.getChunks(doc.id);
      setChunks(data);
    } catch (err) {
      console.error("Failed to load chunks:", err);
      setChunks([]);
    } finally {
      setIsLoadingChunks(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* AI Extraction Engine Status Banner */}
      <div className="rounded-xl p-4 bg-gradient-to-r from-blue-50/80 via-slate-50 to-indigo-50/50 dark:from-slate-900 dark:via-slate-900/90 dark:to-blue-950/30 border border-blue-200/70 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-600/10 dark:bg-brand-500/20 border border-brand-500/30 flex items-center justify-center shrink-0">
            <Cpu className="w-5 h-5 text-brand-600 dark:text-brand-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                AI Extraction Engine:
              </span>
              {aiStatus?.is_live_configured ? (
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Google Gemini 2.0 Flash Active ({aiStatus.masked_key})
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                  Offline Rule & Table Parser Active
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
              {aiStatus?.is_live_configured
                ? "Universal multimodal extraction active. Processes any invoice, quotation, PO, contract, or complex layout."
                : "Standard deterministic parser active. Connect your Google AI Studio API key for zero-shot extraction on any custom layout."}
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            setShowAiConfigModal(true);
            setAiConfigMessage(null);
          }}
          className="self-start sm:self-center px-3 py-1.5 rounded-lg text-xs font-semibold bg-white dark:bg-slate-800 text-brand-700 dark:text-brand-300 border border-brand-500/30 hover:bg-brand-50 dark:hover:bg-slate-700 transition flex items-center gap-1.5 shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5 text-brand-500" />
          <span>{aiStatus?.is_live_configured ? "Configure AI Key" : "Connect Gemini AI Key"}</span>
        </button>
      </div>

      {/* Upload Zone */}
      <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-brand-600 dark:text-brand-400" />
              <span>Universal Commercial Document Ingestion</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Upload invoices, quotations, contracts, or POs (PDF / CSV) in arbitrary global formats.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowDemoLibrary(true)}
              className="px-3.5 py-1.5 bg-brand-600/10 hover:bg-brand-600/20 text-brand-700 dark:text-brand-300 border border-brand-500/30 rounded-lg text-xs font-semibold transition flex items-center gap-1.5 shadow-sm"
              title="Preselect and preview realistic sample invoices, quotes, agreements, and purchase orders"
            >
              <Sparkles className="w-4 h-4 text-brand-500" />
              <span>Demo Document Library</span>
            </button>
          </div>
        </div>

        <form onSubmit={handleUpload} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* File Input */}
            <div className="md:col-span-2 space-y-1">
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400">
                Select File (PDF or CSV, max 10MB)
              </label>
              <input
                type="file"
                accept=".pdf,.csv"
                onChange={(e) => setSelectedFile(e.target.files[0])}
                className="w-full text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg file:mr-4 file:py-2.5 file:px-4 file:rounded-l-lg file:border-0 file:text-xs file:font-semibold file:bg-brand-600 file:text-white hover:file:bg-brand-500 cursor-pointer"
              />
            </div>

            {/* Document Category */}
            <div className="space-y-1">
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400">
                Document Category
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg py-2.5 px-3 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-brand-500"
              >
                <option value="invoice">Invoice (Global / Any Layout)</option>
                <option value="quotation">Quotation / Price Estimate</option>
                <option value="agreement">Agreement / Contract / SOW</option>
                <option value="purchase_order">Purchase Order (PO)</option>
                <option value="other">Other Commercial File</option>
              </select>
            </div>

            {/* Target Project Assignment */}
            <div className="md:col-span-3 space-y-1">
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                <FolderKanban className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
                <span>Assign to Audit Project Baseline (Recommended)</span>
              </label>
              <select
                value={targetProjectId}
                onChange={(e) => setTargetProjectId(e.target.value)}
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-900 dark:text-slate-200 focus:outline-none focus:border-brand-500"
              >
                <option value="">No Project Assigned (Global Workspace)</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.code}) — Vendor: {p.vendor_name} (Cap: ₹{p.budget_amount})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Idempotency Key */}
          <div className="flex items-center gap-3">
            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-[11px] text-slate-600 dark:text-slate-400 flex items-center gap-1">
                  <Key className="w-3 h-3 text-slate-400 dark:text-slate-500" />
                  <span>Idempotency-Key (Optional Header)</span>
                </label>
                <button
                  type="button"
                  onClick={generateKey}
                  className="text-[10px] text-brand-600 dark:text-brand-400 hover:underline"
                >
                  Generate New
                </button>
              </div>
              <input
                type="text"
                value={idempotencyKey}
                onChange={(e) => setIdempotencyKey(e.target.value)}
                placeholder="Unique client key e.g. req_8a72b"
                className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg py-1.5 px-3 text-xs text-slate-900 dark:text-slate-200 font-mono focus:outline-none focus:border-brand-500"
              />
            </div>

            <div className="self-end">
              <button
                type="submit"
                disabled={!selectedFile || isUploading}
                className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition flex items-center gap-2 shadow-lg shadow-brand-600/30"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Uploading...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-4 h-4" />
                    <span>Upload & Enqueue</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {uploadMessage && (
            <div
              className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                uploadMessage.type === "success"
                  ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60"
                  : "bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60"
              }`}
            >
              {uploadMessage.type === "success" ? (
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
              ) : (
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
              )}
              <span>{uploadMessage.text}</span>
            </div>
          )}
        </form>
      </div>

      {/* Documents Queue Table */}
      <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 space-y-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-brand-600 dark:text-brand-400" />
            <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200">
              Document Processing Queue ({documents.length})
            </h3>
          </div>
          <button
            onClick={fetchDocuments}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            title="Refresh"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
            <thead className="bg-slate-50 dark:bg-slate-950/60 uppercase text-[10px] text-slate-500 dark:text-slate-400 font-semibold tracking-wider border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Document</th>
                <th className="py-2.5 px-3">Project Baseline</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Processing</th>
                <th className="py-2.5 px-3">Extracted Invoices & AI Result</th>
                <th className="py-2.5 px-3">Ingested At</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400 dark:text-slate-500 text-xs">
                    No documents ingested yet. Upload an invoice or select from the Demo Document Library above.
                  </td>
                </tr>
              ) : (
                documents.map((d) => {
                  const linkedProj = projects.find((p) => p.id === d.project_id);
                  const hasInvoices = typeof d.extracted_count === "number" && d.extracted_count > 0;
                  const hasZeroRecords = d.status === "done" && (!d.extracted_count || d.extracted_count === 0);

                  return (
                    <tr key={d.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition">
                      <td className="py-2.5 px-3 font-medium text-slate-900 dark:text-slate-200 flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400 shrink-0" />
                        <span className="truncate max-w-[200px]" title={d.filename}>
                          {d.filename}
                        </span>
                      </td>

                      <td className="py-2.5 px-3 text-[11px]">
                        {linkedProj ? (
                          <span className="inline-flex items-center gap-1 font-mono font-semibold px-2 py-0.5 rounded bg-brand-500/10 text-brand-700 dark:text-brand-300 border border-brand-500/20">
                            <FolderKanban className="w-3 h-3 text-brand-600 dark:text-brand-400" />
                            {linkedProj.code}
                          </span>
                        ) : (
                          <span className="text-slate-400 font-mono text-[10px]">—</span>
                        )}
                      </td>

                      <td className="py-2.5 px-3 uppercase text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                        {d.detected_document_type || d.type}
                      </td>

                      <td className="py-2.5 px-3">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold ${
                            d.status === "done"
                              ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20"
                              : d.status === "processing"
                              ? "bg-brand-500/20 text-brand-700 dark:text-brand-300 border border-brand-500/30 animate-pulse"
                              : d.status === "failed"
                              ? "bg-rose-500/20 text-rose-700 dark:text-rose-400 border border-rose-500/30"
                              : "bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20"
                          }`}
                        >
                          {d.status}
                        </span>
                      </td>

                      <td className="py-2.5 px-3">
                        {hasInvoices ? (
                          <button
                            onClick={() => handleOpenDiagnostics(d)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/40 dark:hover:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60 transition group cursor-pointer"
                            title="Click to view full extraction summary and diagnostics"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                            <span>
                              {d.extracted_count} Invoice{d.extracted_count > 1 ? "s" : ""} Extracted
                            </span>
                            <Info className="w-3 h-3 opacity-60 group-hover:opacity-100 shrink-0" />
                          </button>
                        ) : hasZeroRecords ? (
                          <button
                            onClick={() => handleOpenDiagnostics(d)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 dark:hover:bg-amber-900/40 text-amber-700 dark:text-amber-400 border border-amber-300 dark:border-amber-700/60 transition group cursor-pointer animate-pulse"
                            title="Click to see why 0 records were recognized and how to resolve"
                          >
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
                            <span>0 Records Detected • View Details</span>
                            <Info className="w-3 h-3 opacity-60 group-hover:opacity-100 shrink-0" />
                          </button>
                        ) : d.status === "failed" ? (
                          <button
                            onClick={() => handleOpenDiagnostics(d)}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 dark:hover:bg-rose-900/40 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800/60 transition group cursor-pointer"
                            title="Click to view failure details"
                          >
                            <AlertCircle className="w-3.5 h-3.5 text-rose-600 dark:text-rose-400 shrink-0" />
                            <span>Failed • View Error</span>
                            <Info className="w-3 h-3 opacity-60 group-hover:opacity-100 shrink-0" />
                          </button>
                        ) : (
                          <span className="text-[11px] text-slate-400 font-mono">Parsing file...</span>
                        )}
                      </td>

                      <td className="py-2.5 px-3 text-[11px] text-slate-500 dark:text-slate-400">
                        {new Date(d.created_at).toLocaleTimeString()}
                      </td>

                      <td className="py-2.5 px-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleOpenDiagnostics(d)}
                            className="px-2 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded text-[11px] font-medium transition inline-flex items-center gap-1"
                            title="View Extraction Diagnostics"
                          >
                            <Info className="w-3 h-3 text-brand-600 dark:text-brand-400" />
                            <span>Details</span>
                          </button>
                          <button
                            onClick={() => openChunksModal(d)}
                            className="px-2 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-brand-900/40 text-brand-600 dark:text-brand-300 border border-slate-200 dark:border-slate-700 rounded text-[11px] font-medium transition inline-flex items-center gap-1"
                            title="Inspect Text & Vector Chunks"
                          >
                            <Layers className="w-3 h-3 text-brand-600 dark:text-brand-400" />
                            <span>Chunks</span>
                          </button>
                          <button
                            onClick={() => handleDeleteClick(d)}
                            className="p-1 rounded text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-transparent hover:border-rose-200 dark:hover:border-rose-800 transition"
                            title="Delete Document"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Demo Documents Library Modal */}
      {showDemoLibrary && (
        <div className="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-4xl p-6 space-y-5 shadow-2xl my-8 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                    Commercial Demo Document Library
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Preselected real-world invoices, quotations, contracts, and POs with planted anomalies for testing.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowDemoLibrary(false)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 overflow-y-auto p-1 flex-1">
              {DEMO_DOCUMENTS.map((doc) => (
                <div
                  key={doc.id}
                  className="rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 p-4 space-y-3 flex flex-col justify-between hover:border-brand-500 transition"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-brand-500/10 text-brand-700 dark:text-brand-300 font-mono">
                        {doc.categoryLabel}
                      </span>
                      <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {doc.amount}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">
                      {doc.title}
                    </h4>
                    <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
                      {doc.summary}
                    </p>

                    <div className="text-[10px] font-mono text-slate-500 space-y-0.5">
                      <div>Vendor: <span className="text-slate-800 dark:text-slate-200">{doc.vendor}</span></div>
                      <div>Expected: <span className="text-amber-600 dark:text-amber-400 font-medium">{doc.statusOutcome}</span></div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-end gap-2">
                    <button
                      onClick={() => setPreviewDoc(doc)}
                      className="px-3 py-1.5 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded text-xs font-medium border border-slate-200 dark:border-slate-700 flex items-center gap-1.5 transition"
                    >
                      <Eye className="w-3.5 h-3.5 text-slate-500" />
                      <span>Preview Document</span>
                    </button>
                    <button
                      onClick={() => handleIngestDemoDoc(doc)}
                      disabled={isUploading}
                      className="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded text-xs font-semibold flex items-center gap-1.5 shadow-sm transition"
                    >
                      <span>Ingest & Run</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Document Visual Layout Preview Modal */}
      {previewDoc && (
        <div className="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-3xl p-6 md:p-8 space-y-6 shadow-2xl my-6 max-h-[92vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Receipt className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                    Commercial Document Preview
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                    {previewDoc.filename} ({previewDoc.categoryLabel})
                  </p>
                </div>
              </div>
              <button
                onClick={() => setPreviewDoc(null)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Rendered Document Sheet */}
            <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl p-6 space-y-6 overflow-y-auto flex-1 font-sans text-xs">
              {/* Document Header & Badge */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
                <div>
                  <div className="text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                    {previewDoc.preview.vendorName}
                  </div>
                  <div className="text-slate-500 text-[11px] leading-relaxed max-w-sm">
                    {previewDoc.preview.vendorAddress}
                  </div>
                  <div className="text-slate-700 dark:text-slate-300 font-mono font-semibold pt-1">
                    {previewDoc.preview.vendorTaxId}
                  </div>
                </div>

                <div className="text-left sm:text-right space-y-1">
                  <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-brand-600 text-white uppercase tracking-wider inline-block">
                    {previewDoc.preview.docType}
                  </span>
                  <div className="text-[11px] text-slate-500 font-mono">
                    Doc #: <strong className="text-slate-900 dark:text-slate-100">{previewDoc.number}</strong>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Date: {previewDoc.preview.invoiceDate}
                  </div>
                </div>
              </div>

              {/* Bill To & PO Section */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-[11px]">
                <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Billed / Issued To</span>
                  <div className="font-semibold text-slate-900 dark:text-slate-100">{previewDoc.preview.billTo}</div>
                  <div className="text-slate-500">{previewDoc.preview.billToAddress}</div>
                </div>
                <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Order & Terms</span>
                  <div>PO Reference: <span className="font-mono font-semibold text-brand-600 dark:text-brand-400">{previewDoc.preview.poNumber}</span></div>
                  <div>Terms: <span className="text-slate-600 dark:text-slate-300">{previewDoc.preview.paymentTerms}</span></div>
                </div>
              </div>

              {/* Line Items Table */}
              <div className="border border-slate-200 dark:border-slate-800 rounded-lg overflow-hidden bg-white dark:bg-slate-900">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 dark:bg-slate-800/80 uppercase text-[10px] text-slate-600 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-700">
                    <tr>
                      <th className="py-2.5 px-3">Description</th>
                      <th className="py-2.5 px-3 text-center">Qty</th>
                      <th className="py-2.5 px-3 text-right">Unit Rate</th>
                      <th className="py-2.5 px-3 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {previewDoc.preview.lineItems.map((item, iIdx) => (
                      <tr key={iIdx}>
                        <td className="py-2.5 px-3 font-medium text-slate-900 dark:text-slate-200">{item.desc}</td>
                        <td className="py-2.5 px-3 text-center text-slate-600 dark:text-slate-400">{item.qty}</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-600 dark:text-slate-400">{item.rate}</td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900 dark:text-slate-100">{item.amount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Totals & Tax */}
              <div className="flex justify-end text-xs">
                <div className="w-64 space-y-1.5 p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <div className="flex justify-between text-slate-500">
                    <span>Subtotal:</span>
                    <span className="font-mono text-slate-800 dark:text-slate-200">{previewDoc.preview.subtotal}</span>
                  </div>
                  <div className="flex justify-between text-slate-500">
                    <span>{previewDoc.preview.taxRate}:</span>
                    <span className="font-mono text-slate-800 dark:text-slate-200">{previewDoc.preview.taxAmount}</span>
                  </div>
                  <div className="flex justify-between font-bold text-sm pt-1.5 border-t border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100">
                    <span>Net Total:</span>
                    <span className="font-mono text-brand-600 dark:text-brand-400">{previewDoc.preview.totalAmount}</span>
                  </div>
                </div>
              </div>

              {/* Notes & Signatory */}
              <div className="pt-2 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 text-[11px] text-slate-500">
                <div className="italic max-w-md">{previewDoc.preview.notes}</div>
                <div className="font-semibold text-slate-700 dark:text-slate-300">Authorized: {previewDoc.preview.signatory}</div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="pt-2 flex justify-between items-center border-t border-slate-200 dark:border-slate-800">
              <span className="text-xs text-amber-600 dark:text-amber-400 font-medium">
                Expected Finding: {previewDoc.statusOutcome}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPreviewDoc(null)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-medium transition"
                >
                  Close
                </button>
                <button
                  onClick={() => handleIngestDemoDoc(previewDoc)}
                  disabled={isUploading}
                  className="px-5 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold transition flex items-center gap-2 shadow-md shadow-brand-600/30"
                >
                  <span>Ingest This Document Now</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chunks & Vector Inspector Modal */}
      {inspectDoc && (
        <div className="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    Document Chunks & pgvector Index
                  </h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                    {inspectDoc.filename} • {chunks.length} Chunks
                  </p>
                </div>
              </div>
              <button
                onClick={() => setInspectDoc(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-5 overflow-y-auto space-y-3 flex-1">
              {isLoadingChunks ? (
                <div className="py-12 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin text-brand-500" />
                  <span>Loading pgvector chunks...</span>
                </div>
              ) : chunks.length === 0 ? (
                <div className="py-12 text-center text-slate-400 dark:text-slate-500 text-xs">
                  No chunks generated yet. Document is still being processed by Celery worker.
                </div>
              ) : (
                chunks.map((c) => (
                  <div
                    key={c.id}
                    className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/80 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                      <span className="font-mono text-brand-600 dark:text-brand-400 font-semibold">
                        Chunk #{c.chunk_index}
                      </span>
                      <div className="flex items-center gap-2 font-mono text-[10px]">
                        <span className="bg-slate-200 dark:bg-slate-800 px-1.5 py-0.5 rounded text-slate-700 dark:text-slate-300">
                          Page {c.page || 1}
                        </span>
                        <span className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20 px-1.5 py-0.5 rounded">
                          pgvector 1536d
                        </span>
                      </div>
                    </div>
                    <p className="text-slate-800 dark:text-slate-300 leading-relaxed font-mono text-[11px] bg-white dark:bg-slate-900/60 p-2.5 rounded border border-slate-200 dark:border-slate-800/60 break-words whitespace-pre-wrap">
                      {c.text}
                    </p>
                  </div>
                ))
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-end">
              <button
                onClick={() => setInspectDoc(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-medium transition"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Google AI Studio (Gemini) API Key Configuration Modal */}
      {showAiConfigModal && (
        <div className="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-lg p-6 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-brand-600/10 dark:bg-brand-500/20 border border-brand-500/30 flex items-center justify-center text-brand-600 dark:text-brand-400">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    Connect Google AI Studio (Gemini 2.0 Flash)
                  </h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Universal multimodal understanding for any invoice, PO, quotation, or agreement.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowAiConfigModal(false)}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleConfigureAi} className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Google AI Studio API Key
                </label>
                <input
                  type="password"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder="AIzaSy..."
                  required
                  className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg py-2 px-3 text-xs text-slate-900 dark:text-slate-200 font-mono focus:outline-none focus:border-brand-500"
                />
                <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                  <span>Free keys available at Google AI Studio</span>
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
                  >
                    <span>Get Key</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>

              {aiStatus?.is_live_configured && (
                <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800/60 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  <span>
                    Currently active: <strong>Google Gemini 2.0 Flash</strong> ({aiStatus.masked_key}). Entering a new key will verify and replace it.
                  </span>
                </div>
              )}

              {aiConfigMessage && (
                <div
                  className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                    aiConfigMessage.type === "success"
                      ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60"
                      : "bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60"
                  }`}
                >
                  {aiConfigMessage.type === "success" ? (
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
                  )}
                  <span>{aiConfigMessage.text}</span>
                </div>
              )}

              <div className="pt-2 flex justify-end gap-2 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAiConfigModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isConfiguringAi || !apiKeyInput.trim()}
                  className="px-5 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition flex items-center gap-2 shadow-md shadow-brand-600/30"
                >
                  {isConfiguringAi ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Verifying with Google...</span>
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>Verify & Save Key</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Document Extraction Diagnostics & Inspection Modal */}
      {diagnosticsDoc && (
        <div className="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-brand-600/10 dark:bg-brand-500/20 border border-brand-500/30 flex items-center justify-center text-brand-600 dark:text-brand-400">
                  <Info className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    Document Diagnostics & Extraction Audit
                  </h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                    {diagnosticsDoc.filename}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setDiagnosticsDoc(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-700 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 overflow-y-auto space-y-4 text-xs">
              {/* Status Header Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-medium uppercase">
                    Status
                  </span>
                  <span className="font-bold text-xs capitalize text-slate-900 dark:text-slate-100 mt-1 block">
                    {diagnosticsDoc.status}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-medium uppercase">
                    Extracted Records
                  </span>
                  <span
                    className={`font-bold text-xs mt-1 block ${
                      diagnosticsDoc.extracted_count > 0
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-amber-600 dark:text-amber-400"
                    }`}
                  >
                    {diagnosticsDoc.extracted_count || 0} Invoices
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-medium uppercase">
                    Engine Used
                  </span>
                  <span
                    className="font-mono text-[11px] text-slate-900 dark:text-slate-100 mt-1 block truncate"
                    title={diagnosticsDoc.ai_model_used || "Standard Parser"}
                  >
                    {diagnosticsDoc.ai_model_used || "Deterministic Parser"}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-medium uppercase">
                    Project Baseline
                  </span>
                  <span className="font-mono text-[11px] text-slate-900 dark:text-slate-100 mt-1 block truncate">
                    {projects.find((p) => p.id === diagnosticsDoc.project_id)?.code || "None"}
                  </span>
                </div>
              </div>

              {/* Extraction Summary */}
              {diagnosticsDoc.extraction_summary && (
                <div className="p-3.5 rounded-xl bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200/80 dark:border-blue-900/40 text-blue-900 dark:text-blue-200 space-y-1">
                  <span className="font-semibold text-xs flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                    <span>Extraction Summary</span>
                  </span>
                  <p className="text-[11px] leading-relaxed">
                    {diagnosticsDoc.extraction_summary}
                  </p>
                </div>
              )}

              {/* Warning / Error Message if 0 records extracted */}
              {(!diagnosticsDoc.extracted_count || diagnosticsDoc.extracted_count === 0) && (
                <div className="p-4 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800/80 text-amber-900 dark:text-amber-200 space-y-2.5">
                  <div className="flex items-center gap-2 font-bold text-xs text-amber-800 dark:text-amber-300">
                    <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                    <span>Diagnostic Alert: 0 Commercial Records Found</span>
                  </div>
                  <p className="text-[11px] leading-relaxed">
                    {diagnosticsDoc.error_message ||
                      "The parser could not detect valid commercial invoice records (vendor name, invoice reference, and total amount) in this document."}
                  </p>
                  <div className="pt-2 border-t border-amber-200 dark:border-amber-800/60 text-[11px] space-y-1">
                    <span className="font-semibold block">How to resolve this:</span>
                    <ul className="list-disc pl-4 space-y-0.5 text-amber-800/90 dark:text-amber-300/90">
                      <li>
                        Ensure your CSV headers include identifiable names (e.g. <code>invoice_id</code>, <code>vendor_name</code>, <code>total_amount</code>).
                      </li>
                      <li>
                        For custom layouts, non-standard tables, or scanned PDFs, connect your <strong>Google AI Studio Gemini API key</strong> at the top to enable zero-shot AI recognition.
                      </li>
                    </ul>
                  </div>
                </div>
              )}

              {/* Invoices List for This Document */}
              <div className="space-y-2">
                <span className="font-semibold text-xs text-slate-800 dark:text-slate-200 block">
                  Extracted Commercial Invoices ({docInvoices.length})
                </span>

                {isLoadingDocInvoices ? (
                  <div className="py-6 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-brand-500" />
                    <span>Loading invoice records...</span>
                  </div>
                ) : docInvoices.length === 0 ? (
                  <div className="py-6 text-center text-slate-400 dark:text-slate-500 text-xs border border-dashed border-slate-200 dark:border-slate-800 rounded-xl">
                    No individual invoices persisted for this file.
                  </div>
                ) : (
                  <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 dark:bg-slate-950/60 text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400">
                        <tr>
                          <th className="py-2 px-3">Invoice #</th>
                          <th className="py-2 px-3">Vendor</th>
                          <th className="py-2 px-3">Gross Total</th>
                          <th className="py-2 px-3">Paid Amount</th>
                          <th className="py-2 px-3">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {docInvoices.map((inv) => (
                          <tr key={inv.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30">
                            <td className="py-2 px-3 font-mono font-semibold text-brand-600 dark:text-brand-400">
                              {inv.invoice_number}
                            </td>
                            <td className="py-2 px-3 text-slate-800 dark:text-slate-200 truncate max-w-[140px]">
                              {inv.vendor_name}
                            </td>
                            <td className="py-2 px-3 font-semibold text-slate-900 dark:text-slate-100">
                              ₹{parseFloat(inv.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </td>
                            <td className="py-2 px-3 font-semibold text-emerald-600 dark:text-emerald-400">
                              ₹{parseFloat(inv.paid_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </td>
                            <td className="py-2 px-3">
                              <span
                                className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold ${
                                  inv.payment_status === "paid"
                                    ? "bg-emerald-500/10 text-emerald-600"
                                    : inv.payment_status === "partially_paid"
                                    ? "bg-blue-500/10 text-blue-600"
                                    : "bg-amber-500/10 text-amber-600"
                                }`}
                              >
                                {inv.payment_status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center">
              <button
                onClick={() => {
                  const target = diagnosticsDoc;
                  setDiagnosticsDoc(null);
                  openChunksModal(target);
                }}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-brand-600 dark:text-brand-300 rounded-lg text-xs font-medium transition flex items-center gap-1.5"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Inspect Text Chunks</span>
              </button>

              <button
                onClick={() => setDiagnosticsDoc(null)}
                className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white text-white dark:text-slate-900 rounded-lg text-xs font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tailwind Confirm Delete Modal */}
      <ConfirmModal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Ingested Document"
        message="Permanently remove this commercial file and its vector chunks from pgvector. Extracted invoices will be preserved unless explicitly deleted."
        itemName={deleteTarget?.name}
        confirmLabel="Delete Document"
        isLoading={isDeleting}
      />
    </div>
  );
}

