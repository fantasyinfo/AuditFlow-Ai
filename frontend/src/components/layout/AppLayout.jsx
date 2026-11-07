import React from "react";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";

export default function AppLayout({ currentModule, onSelectModule, moduleTitle, children }) {
  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 overflow-hidden transition-colors">
      {/* Navigation Sidebar */}
      <Sidebar currentModule={currentModule} onSelectModule={onSelectModule} />

      {/* Main App Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <Navbar
          currentModuleTitle={moduleTitle}
          onNavigateDocs={() => onSelectModule("docs")}
        />

        {/* Scrollable Viewport */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-100/70 dark:bg-gradient-to-b dark:from-slate-900/20 dark:to-slate-950 transition-colors">
          <div className="max-w-7xl mx-auto space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

