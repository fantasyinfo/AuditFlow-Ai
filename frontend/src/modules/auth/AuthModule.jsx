import React, { useState } from "react";
import {
  ShieldCheck,
  Lock,
  Mail,
  Building,
  Key,
  Shuffle,
  ArrowRight,
  AlertCircle,
  Sparkles,
  Sun,
  Moon,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";

export default function AuthModule() {
  const { login, register, createRandomTenant, isLoading } = useAuth();
  const { theme, toggleTheme, isDark } = useTheme();
  const [tab, setTab] = useState("login"); // "login" | "register"

  // Login form state
  const [loginEmail, setLoginEmail] = useState("admin@acme.com");
  const [loginPassword, setLoginPassword] = useState("SecurePassword123!");

  // Register form state
  const [regTenant, setRegTenant] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");

  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(loginEmail, loginPassword);
    } catch (err) {
      setError(err.message || "Invalid credentials");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register(regTenant, regEmail, regPassword);
    } catch (err) {
      setError(err.message || "Registration failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickDemoTenant = async () => {
    setError(null);
    setIsSubmitting(true);
    try {
      await createRandomTenant();
    } catch (err) {
      setError(err.message || "Failed to generate tenant");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center items-center p-4 selection:bg-brand-500 selection:text-white relative overflow-hidden transition-colors">
      {/* Top Bar Controls */}
      <div className="absolute top-5 right-5 z-20">
        <button
          onClick={toggleTheme}
          className="p-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:text-brand-600 dark:hover:text-brand-400 shadow-sm transition"
          title={`Switch to ${isDark ? "Light" : "Dark"} Mode`}
        >
          {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
        </button>
      </div>

      {/* Background Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-brand-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-72 h-72 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md space-y-6 relative z-10">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-500 items-center justify-center text-white shadow-xl shadow-brand-500/30 mb-1">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            AuditFlow AI
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            AP Audit & Fraud Detection Admin Platform
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl bg-white/95 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 p-6 md:p-8 space-y-5 shadow-2xl backdrop-blur-xl transition-colors">
          {/* Tab Selector */}
          <div className="flex border-b border-slate-200 dark:border-slate-800 text-xs font-semibold">
            <button
              onClick={() => {
                setTab("login");
                setError(null);
              }}
              className={`flex-1 pb-3 text-center border-b-2 transition ${
                tab === "login"
                  ? "border-brand-500 text-brand-600 dark:text-brand-400"
                  : "border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setTab("register");
                setError(null);
              }}
              className={`flex-1 pb-3 text-center border-b-2 transition ${
                tab === "register"
                  ? "border-brand-500 text-brand-600 dark:text-brand-400"
                  : "border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              }`}
            >
              Register Tenant
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Login Form */}
          {tab === "login" && (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                    placeholder="auditor@company.com"
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                    placeholder="••••••••"
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-semibold transition flex items-center justify-center gap-2 shadow-lg shadow-brand-600/30"
              >
                <span>{isSubmitting ? "Authenticating..." : "Sign In to Admin Center"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* Register Form */}
          {tab === "register" && (
            <form onSubmit={handleRegisterSubmit} className="space-y-4">
              <div className="space-y-1">
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Organization / Tenant Name
                </label>
                <div className="relative">
                  <Building className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={regTenant}
                    onChange={(e) => setRegTenant(e.target.value)}
                    required
                    placeholder="e.g. Apex Global Corp"
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Admin Email
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="email"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    required
                    placeholder="admin@apex.com"
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Password (min 8 characters)
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="password"
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    required
                    minLength={8}
                    placeholder="••••••••"
                    className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/30"
              >
                <span>{isSubmitting ? "Creating..." : "Register Organization & Enter"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {/* Quick Demo Multi-Tenant Button */}
          <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={handleQuickDemoTenant}
              disabled={isSubmitting}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800/80 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 hover:text-brand-600 dark:hover:text-brand-300 border border-slate-200 dark:border-slate-700/80 rounded-lg text-xs font-medium transition flex items-center justify-center gap-2 shadow-sm"
            >
              <Shuffle className="w-3.5 h-3.5 text-brand-500 dark:text-brand-400" />
              <span>Instant Test Tenant (1-Click Generator)</span>
            </button>
            <p className="text-[10px] text-slate-400 dark:text-slate-500 text-center mt-2">
              Automatically creates a new isolated organization to test multi-tenancy boundaries.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

