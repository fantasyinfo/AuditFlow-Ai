import React, { useState, useRef, useEffect } from "react";
import {
  Bot,
  Send,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Layers,
  FileText,
  CornerDownLeft,
} from "lucide-react";
import { api } from "../../api/client";

export default function AssistantModule() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I am your AuditFlow AI assistant powered by Google AI Studio (Gemini) and pgvector RAG. I can analyze your uploaded invoices, quotations, contracts, and audit findings with mandatory citations. How can I assist your audit investigation today?",
      citations: [],
      answeredFromSources: false,
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const quickPrompts = [
    { label: "🔍 Check Duplicates", query: "Are there any duplicate invoices detected?" },
    { label: "🏢 Sharma Traders Findings", query: "What findings are flagged for Sharma Traders?" },
    { label: "📋 Missing Purchase Orders", query: "Are there any invoices missing supporting purchase orders?" },
    { label: "📄 Details of INV-1042", query: "What is the total amount and invoice date of invoice INV-1042?" },
    { label: "🛡️ Test Refusal Guardrail", query: "Who is the chief operating officer of Galactic Freight Systems?" },
    { label: "🔒 Test Read-Only Guardrail", query: "Please delete invoice INV-1042 and confirm all findings immediately." },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (queryToSend) => {
    const q = (queryToSend || inputQuery).trim();
    if (!q || isLoading) return;

    const newMessages = [...messages, { role: "user", content: q }];
    setMessages(newMessages);
    setInputQuery("");
    setIsLoading(true);

    try {
      const res = await api.assistant.ask(q);
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: res.answer,
          citations: res.citations || [],
          answeredFromSources: res.answered_from_sources,
        },
      ]);
    } catch (err) {
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content: `Error: ${err.message || "Failed to communicate with AI Assistant."}`,
          citations: [],
          answeredFromSources: false,
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        role: "assistant",
        content: "Conversation history cleared. How can I help you audit your commercial documents?",
        citations: [],
        answeredFromSources: false,
      },
    ]);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] rounded-xl bg-slate-900 border border-slate-800 overflow-hidden shadow-2xl">
      {/* Assistant Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-purple-500/25">
            <Sparkles className="w-5 h-5 text-purple-200" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-100">
                AI Audit Assistant
              </h2>
              <span className="text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded font-mono">
                Google AI Studio Gemini + RAG
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Natural language intelligence with mandatory citations across all documents
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden sm:inline-block text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            Strictly Read-Only
          </span>
          <span className="hidden sm:inline-block text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Mandatory Citations
          </span>
          <button
            onClick={clearChat}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            title="Clear Chat"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Suggested Quick Prompt Pills */}
      <div className="px-4 py-2.5 border-b border-slate-800/80 bg-slate-950/30 flex items-center gap-2 overflow-x-auto text-xs shrink-0">
        <span className="text-[11px] text-slate-400 font-medium shrink-0">Prompts:</span>
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p.query)}
            disabled={isLoading}
            className="px-2.5 py-1 rounded-md bg-slate-800/70 hover:bg-purple-900/40 text-purple-200 border border-slate-700/80 hover:border-purple-500/40 text-[11px] font-medium transition shrink-0"
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Chat Messages Thread */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
        {messages.map((m, index) => {
          const isUser = m.role === "user";
          return (
            <div
              key={index}
              className={`flex items-start gap-3 ${isUser ? "justify-end" : "justify-start"}`}
            >
              {!isUser && (
                <div className="w-7 h-7 rounded-lg bg-purple-600/30 border border-purple-500/30 flex items-center justify-center text-purple-300 shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`rounded-2xl p-4 max-w-[85%] sm:max-w-[75%] space-y-2 text-xs leading-relaxed ${
                  isUser
                    ? "bg-brand-600 text-white rounded-tr-sm shadow-md shadow-brand-600/20"
                    : m.isError
                    ? "bg-rose-950/40 border border-rose-800 text-rose-200 rounded-tl-sm"
                    : "bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-sm shadow-lg"
                }`}
              >
                {!isUser && (
                  <div className="flex items-center justify-between gap-3 pb-1 border-b border-slate-800/60 text-[10px]">
                    <span className="font-semibold text-purple-400 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      <span>AuditFlow Intelligence</span>
                    </span>

                    {m.answeredFromSources ? (
                      <span className="inline-flex items-center gap-1 text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-1.5 py-0.5 rounded font-mono">
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        <span>Verified from documents</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-amber-400 bg-amber-950/60 border border-amber-800/60 px-1.5 py-0.5 rounded font-mono">
                        <ShieldCheck className="w-2.5 h-2.5" />
                        <span>Guardrail / Out-of-Domain</span>
                      </span>
                    )}
                  </div>
                )}

                <p className="whitespace-pre-line text-slate-200 text-xs leading-relaxed font-sans">
                  {m.content}
                </p>

                {/* Citation Pills */}
                {m.citations && m.citations.length > 0 && (
                  <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] text-slate-400 font-semibold">Citations:</span>
                    {m.citations.map((cite, cIdx) => (
                      <span
                        key={cIdx}
                        className="px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-800/60 font-mono text-[10px] shadow-sm"
                      >
                        {cite}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-center gap-3 text-slate-400 text-xs py-2">
            <div className="w-7 h-7 rounded-lg bg-purple-600/30 border border-purple-500/30 flex items-center justify-center text-purple-300 shrink-0 animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex items-center gap-2 bg-slate-950 border border-slate-800 px-3 py-2 rounded-xl text-purple-300">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce" />
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce [animation-delay:0.2s]" />
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce [animation-delay:0.4s]" />
              <span className="text-[11px] ml-1 text-slate-400">
                Retrieving vector chunks and executing Google Gemini tools...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/80">
        <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl p-2 focus-within:border-brand-500 transition">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about duplicate invoices, contracts, quotations, GSTIN, or vendor anomalies..."
            className="flex-1 bg-transparent px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputQuery.trim() || isLoading}
            className="p-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-40 text-white rounded-lg transition shadow-md shadow-brand-600/30"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[10px] text-slate-500 mt-2 text-center">
          The AI Assistant is strictly read-only and answers only with explicit citations from your tenant's documents.
        </p>
      </div>
    </div>
  );
}

