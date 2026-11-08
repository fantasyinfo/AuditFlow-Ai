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
} from "lucide-react";
import { api } from "../../api/client";
import { DEMO_DOCUMENTS } from "../../data/demoDocuments";
import { useProject } from "../../context/ProjectContext";

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

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 3000);
    return () => clearInterval(interval);
  }, []);

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

  const handleDeleteDocument = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}" and all its extracted chunks?`)) {
      return;
    }
    try {
      await api.documents.delete(docId);
      await fetchDocuments();
    } catch (err) {
      alert("Failed to delete document: " + err.message);
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
                <th className="py-2.5 px-3">Filename</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Ingested At</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400 dark:text-slate-500 text-xs">
                    No documents ingested yet. Upload an invoice or select from the Demo Document Library above.
                  </td>
                </tr>
              ) : (
                documents.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition">
                    <td className="py-2.5 px-3 font-medium text-slate-900 dark:text-slate-200 flex items-center gap-2">
                      <FileText className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400 shrink-0" />
                      <span className="truncate max-w-xs">{d.filename}</span>
                    </td>
                    <td className="py-2.5 px-3 uppercase text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                      {d.type}
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
                    <td className="py-2.5 px-3 text-[11px] text-slate-500 dark:text-slate-400">
                      {new Date(d.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => openChunksModal(d)}
                          className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-brand-900/40 text-brand-600 dark:text-brand-300 border border-slate-200 dark:border-slate-700 rounded text-[11px] font-medium transition inline-flex items-center gap-1.5"
                          title="Inspect Chunks"
                        >
                          <Layers className="w-3 h-3 text-brand-600 dark:text-brand-400" />
                          <span>Chunks</span>
                        </button>
                        <button
                          onClick={() => handleDeleteDocument(d.id, d.filename)}
                          className="p-1 rounded text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-transparent hover:border-rose-200 dark:hover:border-rose-800 transition"
                          title="Delete Document"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
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
    </div>
  );
}

