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
} from "lucide-react";
import { api } from "../../api/client";

export default function DocumentsModule() {
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);
  const [docType, setDocType] = useState("invoice");
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState(null);

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
      const res = await api.documents.upload(selectedFile, docType, idempotencyKey);
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

  const seedDuplicateInvoice = async () => {
    setIsUploading(true);
    try {
      const csv =
        "vendor,invoice_number,date,amount,gstin\n" +
        "Sharma Traders,INV-1042-DUP,2026-08-12,118000.00,07AAAAA0000A1Z5\n";
      const blob = new Blob([csv], { type: "text/csv" });
      const file = new File([blob], "invoice_1042_dup.csv", { type: "text/csv" });
      await api.documents.upload(file, "invoice");
      setUploadMessage({
        type: "success",
        text: "Seeded intentional duplicate invoice INV-1042-DUP! Rules engine will trigger finding.",
      });
      fetchDocuments();
    } catch (err) {
      setUploadMessage({ type: "error", text: "Failed to seed duplicate" });
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

          <button
            onClick={seedDuplicateInvoice}
            disabled={isUploading}
            className="px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-500/30 rounded-lg text-xs font-semibold transition flex items-center gap-1.5"
            title="Seed duplicate invoice to trigger duplicate_invoice finding"
          >
            <AlertCircle className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
            <span>Seed Test Duplicate</span>
          </button>
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
                    No documents ingested yet. Upload an invoice or agreement above.
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
                      <button
                        onClick={() => openChunksModal(d)}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-brand-900/40 text-brand-600 dark:text-brand-300 border border-slate-200 dark:border-slate-700 rounded text-[11px] font-medium transition inline-flex items-center gap-1.5"
                      >
                        <Layers className="w-3 h-3 text-brand-600 dark:text-brand-400" />
                        <span>Inspect Chunks</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

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

