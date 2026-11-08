import React, { useState, useEffect } from "react";
import {
  Receipt,
  Search,
  DollarSign,
  Calendar,
  Building,
  FileCheck,
  AlertTriangle,
  X,
  RefreshCw,
  Calculator,
  Percent,
  Trash2,
} from "lucide-react";
import { api } from "../../api/client";

export default function InvoicesModule({ onNavigate }) {
  const [invoices, setInvoices] = useState([]);
  const [findings, setFindings] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [removeGST, setRemoveGST] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [invData, findData] = await Promise.all([
        api.invoices.list(50),
        api.findings.list("", "", 100),
      ]);
      setInvoices(invData);
      setFindings(findData);
    } catch (err) {
      console.error("Failed to load invoice records:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredInvoices = invoices.filter((inv) => {
    const term = searchTerm.toLowerCase();
    return (
      (inv.invoice_number && inv.invoice_number.toLowerCase().includes(term)) ||
      (inv.vendor_name && inv.vendor_name.toLowerCase().includes(term)) ||
      (inv.vendor_gstin && inv.vendor_gstin.toLowerCase().includes(term))
    );
  });

  const getInvoiceFindings = (invoiceId) => {
    return findings.filter((f) => f.invoice_id === invoiceId);
  };

  const handleDeleteInvoice = async (invoiceId, invoiceNumber) => {
    if (!window.confirm(`Are you sure you want to delete invoice "${invoiceNumber || invoiceId}" and its findings?`)) {
      return;
    }
    try {
      await api.invoices.delete(invoiceId);
      if (selectedInvoice && selectedInvoice.id === invoiceId) {
        setSelectedInvoice(null);
      }
      await fetchData();
    } catch (err) {
      alert("Failed to delete invoice: " + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Receipt className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <span>Extracted Commercial Records</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Structured financial entries parsed by Gemini / RAG pipeline.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Remove GST Toggle */}
          <button
            onClick={() => setRemoveGST(!removeGST)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold transition border ${
              removeGST
                ? "bg-brand-600 text-white border-brand-500 shadow-sm"
                : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:bg-slate-200"
            }`}
          >
            <Calculator className="w-3.5 h-3.5" />
            <span>{removeGST ? "Viewing: Net (Ex-GST)" : "Remove GST / Net View"}</span>
          </button>

          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search vendor or invoice..."
              className="bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-900 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500 w-64"
            />
          </div>
          <button
            onClick={fetchData}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 transition"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 dark:text-slate-300">
            <thead className="bg-slate-50 dark:bg-slate-950/70 uppercase text-[10px] text-slate-500 dark:text-slate-400 font-semibold tracking-wider border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-3 px-4">Invoice #</th>
                <th className="py-3 px-4">Vendor</th>
                <th className="py-3 px-4">Total Amount</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Tax ID / GSTIN</th>
                <th className="py-3 px-4">Anomalies</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400 dark:text-slate-400 text-xs">
                    Loading extracted invoices...
                  </td>
                </tr>
              ) : filteredInvoices.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400 dark:text-slate-500 text-xs">
                    No commercial records found matching search.
                  </td>
                </tr>
              ) : (
                filteredInvoices.map((inv) => {
                  const invFindings = getInvoiceFindings(inv.id);
                  const hasCrit = invFindings.some((f) => f.severity === "critical");
                  return (
                    <tr
                      key={inv.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition cursor-pointer"
                      onClick={() => setSelectedInvoice(inv)}
                    >
                      <td className="py-3 px-4 font-mono font-medium text-brand-600 dark:text-brand-300">
                        {inv.invoice_number}
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-900 dark:text-slate-200">
                        {inv.vendor_name}
                      </td>
                      <td className="py-3 px-4 font-mono font-medium text-slate-900 dark:text-slate-100">
                        {removeGST ? (
                          <div>
                            <span className="font-bold text-brand-600 dark:text-brand-400 block">
                              ₹
                              {(
                                parseFloat(inv.net_amount) ||
                                parseFloat(inv.total_amount) / 1.18
                              ).toLocaleString("en-IN", {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}
                            </span>
                            <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-sans">
                              Ex-Tax (GST: ₹
                              {(
                                parseFloat(inv.tax_amount) ||
                                parseFloat(inv.total_amount) - parseFloat(inv.total_amount) / 1.18
                              ).toLocaleString("en-IN", {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}
                              )
                            </span>
                          </div>
                        ) : (
                          <span className="font-bold">
                            ₹
                            {parseFloat(inv.total_amount || 0).toLocaleString("en-IN", {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-500 dark:text-slate-400">
                        {inv.invoice_date || "—"}
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-500 dark:text-slate-400">
                        {inv.vendor_gstin || "N/A"}
                      </td>
                      <td className="py-3 px-4">
                        {invFindings.length > 0 ? (
                          <span
                            className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded font-semibold uppercase ${
                              hasCrit
                                ? "bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20"
                                : "bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20"
                            }`}
                          >
                            <AlertTriangle className="w-3 h-3" />
                            <span>{invFindings.length} Flagged</span>
                          </span>
                        ) : (
                          <span className="text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                            Clean
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedInvoice(inv);
                            }}
                            className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded text-[11px] font-medium transition"
                          >
                            Details
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteInvoice(inv.id, inv.invoice_number);
                            }}
                            className="p-1 rounded text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-transparent hover:border-rose-200 dark:hover:border-rose-800 transition"
                            title="Delete Invoice"
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

      {/* Invoice Detail Drawer */}
      {selectedInvoice && (
        <div className="fixed inset-0 bg-slate-900/60 dark:bg-slate-950/80 backdrop-blur-sm flex justify-end z-50">
          <div className="bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 w-full max-w-lg h-full flex flex-col p-6 space-y-6 shadow-2xl overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Receipt className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                    Invoice Details
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                    {selectedInvoice.invoice_number}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Structured Details Grid */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/80 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-semibold">Vendor</span>
                <p className="font-semibold text-slate-900 dark:text-slate-200">{selectedInvoice.vendor_name}</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/80 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-semibold">Amount</span>
                <p className="font-bold text-slate-900 dark:text-slate-100 font-mono">
                  ₹{parseFloat(selectedInvoice.total_amount || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </p>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/80 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-semibold">Invoice Date</span>
                <p className="text-slate-700 dark:text-slate-300 font-mono">{selectedInvoice.invoice_date || "Not detected"}</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/80 space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-semibold">Tax ID / GSTIN</span>
                <p className="text-slate-700 dark:text-slate-300 font-mono">{selectedInvoice.vendor_gstin || "None"}</p>
              </div>
            </div>

            {/* Findings Section */}
            <div className="space-y-3">
              <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-500 dark:text-amber-400" />
                <span>Associated Audit Findings</span>
              </h4>

              {getInvoiceFindings(selectedInvoice.id).length === 0 ? (
                <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/30 text-emerald-800 dark:text-emerald-400 text-xs flex items-center gap-2">
                  <FileCheck className="w-4 h-4" />
                  <span>No audit anomalies or compliance issues identified.</span>
                </div>
              ) : (
                <div className="space-y-2">
                  {getInvoiceFindings(selectedInvoice.id).map((f) => (
                    <div
                      key={f.id}
                      className="p-3 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/80 space-y-1 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-brand-600 dark:text-brand-400 font-semibold">{f.rule}</span>
                        <span className="text-[10px] uppercase font-bold text-rose-700 dark:text-rose-400 bg-rose-500/10 px-1.5 py-0.5 rounded">
                          {f.severity}
                        </span>
                      </div>
                      <p className="text-slate-700 dark:text-slate-300 text-[11px]">{f.reason}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-4 mt-auto">
              <button
                onClick={() => setSelectedInvoice(null)}
                className="w-full py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-semibold transition"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

