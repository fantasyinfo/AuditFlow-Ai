import React from "react";
import {
  LogOut,
  User,
  Sun,
  Moon,
  FolderKanban,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";
import { useProject } from "../../context/ProjectContext";

export default function Navbar({ currentModuleTitle }) {
  const { currentUser, tenant, logout } = useAuth();
  const { toggleTheme, isDark } = useTheme();
  const { projects, selectedProjectId, selectProject } = useProject();

  return (
    <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-6 flex items-center justify-between z-10 transition-colors">
      {/* Current Screen Short Title */}
      <div className="flex items-center gap-3">
        <h1 className="text-base font-bold text-slate-900 dark:text-slate-100 tracking-tight">
          {currentModuleTitle}
        </h1>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Project Selector in Navbar */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 text-xs">
          <FolderKanban className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400 shrink-0" />
          <span className="text-slate-500 dark:text-slate-400 font-medium hidden sm:inline">Project:</span>
          <select
            value={selectedProjectId}
            onChange={(e) => selectProject(e.target.value)}
            className="bg-transparent font-bold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer max-w-[160px] truncate"
          >
            {projects.length === 0 ? (
              <option value="">No Active Projects</option>
            ) : (
              projects.map((p) => (
                <option
                  key={p.id}
                  value={p.id}
                  className="bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100"
                >
                  {p.code} — {p.name}
                </option>
              ))
            )}
          </select>
        </div>

        {/* Light / Dark Mode Toggle (Icon-only, clean & uncluttered) */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition"
          title={`Switch to ${isDark ? "Light" : "Dark"} Mode`}
          aria-label="Toggle light and dark theme"
        >
          {isDark ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-slate-700" />
          )}
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-3 pl-2 sm:pl-3 border-l border-slate-200 dark:border-slate-800">
          <div className="text-right hidden md:block">
            <div className="text-xs font-semibold text-slate-900 dark:text-slate-200">
              {currentUser?.email || "Auditor"}
            </div>
            <div className="text-[10px] text-brand-600 dark:text-brand-400 font-medium uppercase tracking-wider">
              {currentUser?.role || "Admin"} • {tenant?.name || "Tenant"}
            </div>
          </div>

          <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-300">
            <User className="w-4 h-4 text-brand-600 dark:text-brand-400" />
          </div>

          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 dark:hover:text-rose-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
