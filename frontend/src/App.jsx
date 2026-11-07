import React, { useState } from "react";
import { useAuth } from "./context/AuthContext";
import AppLayout from "./components/layout/AppLayout";
import AuthModule from "./modules/auth/AuthModule";
import DashboardModule from "./modules/dashboard/DashboardModule";
import DocumentsModule from "./modules/documents/DocumentsModule";
import InvoicesModule from "./modules/invoices/InvoicesModule";
import FindingsModule from "./modules/findings/FindingsModule";
import RulesModule from "./modules/rules/RulesModule";
import AssistantModule from "./modules/assistant/AssistantModule";
import AuditLogsModule from "./modules/audit-logs/AuditLogsModule";
import DocsModule from "./modules/docs/DocsModule";

const MODULE_TITLES = {
  dashboard: "Executive AP Overview & Risk Dashboard",
  documents: "Document Ingestion & File Processing Queue",
  invoices: "Extracted Commercial Invoices & Metadata",
  findings: "Audit Findings & Fraud Investigation",
  rules: "Audit Rules & Tenant Policy Builder",
  assistant: "AI Audit Assistant (Google AI Studio Gemini + RAG)",
  "audit-logs": "Immutable Compliance & Operations Trail",
  docs: "AuditFlow Platform Guide & Documentation",
};

export default function App() {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentModule, setCurrentModule] = useState("dashboard");

  if (isLoading) {
    return (
      <div className="h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center gap-3 text-slate-500 dark:text-slate-400">
        <div className="w-8 h-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
        <span className="text-xs font-mono">Initializing AuditFlow Admin Center...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthModule />;
  }

  const renderModule = () => {
    switch (currentModule) {
      case "dashboard":
        return <DashboardModule onNavigate={setCurrentModule} />;
      case "documents":
        return <DocumentsModule />;
      case "invoices":
        return <InvoicesModule />;
      case "findings":
        return <FindingsModule />;
      case "rules":
        return <RulesModule />;
      case "assistant":
        return <AssistantModule />;
      case "audit-logs":
        return <AuditLogsModule />;
      case "docs":
        return <DocsModule onNavigate={setCurrentModule} />;
      default:
        return <DashboardModule onNavigate={setCurrentModule} />;
    }
  };

  return (
    <AppLayout
      currentModule={currentModule}
      onSelectModule={setCurrentModule}
      moduleTitle={MODULE_TITLES[currentModule] || "Admin Center"}
    >
      {renderModule()}
    </AppLayout>
  );
}

