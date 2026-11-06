from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["UI"])

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AuditFlow AI — Testing Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { background-color: #0f172a; color: #f8fafc; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .card { background-color: #1e293b; border: 1px solid #334155; border-radius: 0.75rem; }
    .input-box { background-color: #0f172a; border: 1px solid #334155; color: #f8fafc; border-radius: 0.5rem; padding: 0.5rem 0.75rem; }
    .input-box:focus { border-color: #38bdf8; outline: none; }
  </style>
</head>
<body class="min-h-screen p-4 md:p-8">
  <div class="max-w-7xl mx-auto space-y-6">

    <!-- Top Navigation Header -->
    <header class="flex flex-col md:flex-row items-center justify-between card p-6 gap-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-indigo-600 flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-indigo-500/30">
          <i class="fa-solid fa-shield-halved"></i>
        </div>
        <div>
          <h1 class="text-xl font-bold tracking-tight">AuditFlow AI <span class="text-xs bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded border border-indigo-500/30">Day 4 MVP</span></h1>
          <p class="text-xs text-slate-400">AP Audit & Fraud Detection Live Pipeline Tester</p>
        </div>
      </div>
      <div class="flex items-center gap-4 text-sm">
        <div id="healthBadge" class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 text-xs border border-slate-700">
          <span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse" id="healthDot"></span>
          <span id="healthText" class="text-slate-300">Checking API...</span>
        </div>
        <div id="authStatusBadge" class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-rose-500/10 text-rose-400 text-xs border border-rose-500/20">
          <i class="fa-solid fa-lock"></i>
          <span id="authStatusText">Not Authenticated</span>
        </div>
      </div>
    </header>

    <!-- Session & Auth State Banner -->
    <div id="activeSessionBanner" class="hidden card p-4 bg-indigo-950/40 border-indigo-800/50 flex flex-wrap items-center justify-between gap-4 text-xs">
      <div class="space-y-1">
        <p><span class="text-slate-400">Tenant:</span> <strong id="lblTenantName" class="text-indigo-300"></strong> <span class="text-slate-500 text-[10px]" id="lblTenantId"></span></p>
        <p><span class="text-slate-400">User:</span> <strong id="lblUserEmail" class="text-indigo-300"></strong> | Role: <span id="lblUserRole" class="text-indigo-400"></span></p>
      </div>
      <button onclick="logout()" class="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs transition">
        <i class="fa-solid fa-arrow-right-from-bracket mr-1"></i> Sign Out
      </button>
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Column 1: Auth & Operations -->
      <div class="space-y-6">

        <!-- Auth Tabs: Login / Register -->
        <div class="card p-6 space-y-4">
          <div class="flex border-b border-slate-700 text-sm font-medium">
            <button id="tabBtnLogin" onclick="switchAuthTab('login')" class="pb-2 px-4 border-b-2 border-indigo-500 text-indigo-400">Login</button>
            <button id="tabBtnRegister" onclick="switchAuthTab('register')" class="pb-2 px-4 border-b-2 border-transparent text-slate-400 hover:text-slate-200">Register Tenant</button>
          </div>

          <!-- Login Form -->
          <div id="loginForm" class="space-y-3">
            <div>
              <label class="block text-xs text-slate-400 mb-1">Email</label>
              <input id="loginEmail" type="email" class="w-full input-box text-sm" value="admin@acme.com" placeholder="email@company.com">
            </div>
            <div>
              <label class="block text-xs text-slate-400 mb-1">Password</label>
              <input id="loginPassword" type="password" class="w-full input-box text-sm" value="SecurePassword123!" placeholder="••••••••">
            </div>
            <button onclick="handleLogin()" class="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-sm font-medium transition flex items-center justify-center gap-2">
              <i class="fa-solid fa-key"></i> Authenticate
            </button>
          </div>

          <!-- Register Form -->
          <div id="registerForm" class="space-y-3 hidden">
            <div>
              <label class="block text-xs text-slate-400 mb-1">Organization / Tenant Name</label>
              <input id="regTenant" type="text" class="w-full input-box text-sm" placeholder="e.g. Apex Financial Corp">
            </div>
            <div>
              <label class="block text-xs text-slate-400 mb-1">Admin Email</label>
              <input id="regEmail" type="email" class="w-full input-box text-sm" placeholder="admin@apex.com">
            </div>
            <div>
              <label class="block text-xs text-slate-400 mb-1">Password (min 8 chars)</label>
              <input id="regPassword" type="password" class="w-full input-box text-sm" placeholder="••••••••">
            </div>
            <button onclick="handleRegister()" class="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-sm font-medium transition flex items-center justify-center gap-2">
              <i class="fa-solid fa-building"></i> Register Organization
            </button>
          </div>
        </div>

        <!-- Quick Multi-Tenant Generator -->
        <div class="card p-5 space-y-3">
          <h3 class="text-xs font-semibold uppercase text-slate-400 tracking-wider">Multi-Tenancy Tester</h3>
          <p class="text-xs text-slate-400">Instantly generate a separate isolated tenant to test data boundaries.</p>
          <button onclick="generateRandomTenant()" class="w-full py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded text-xs transition flex items-center justify-center gap-2">
            <i class="fa-solid fa-shuffle"></i> Create Random Tenant & Sign In
          </button>
        </div>

        <!-- Seed Duplicate Demo Button -->
        <div class="card p-5 space-y-3 border-amber-500/30 bg-amber-950/20">
          <h3 class="text-xs font-semibold uppercase text-amber-400 tracking-wider flex items-center gap-1.5">
            <i class="fa-solid fa-triangle-exclamation"></i> Seed Test Duplicate
          </h3>
          <p class="text-xs text-slate-400">Uploads an intentional duplicate invoice to trigger the rules engine live.</p>
          <button onclick="seedTestDuplicateInvoice()" class="w-full py-2 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs font-medium transition flex items-center justify-center gap-2">
            <i class="fa-solid fa-clone"></i> Ingest Seeded Duplicate Invoice
          </button>
        </div>

        <!-- Document Chunks Preview Modal/Panel -->
        <div id="chunksCard" class="card p-5 space-y-3 hidden">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-semibold uppercase text-indigo-400 tracking-wider flex items-center gap-1.5">
              <i class="fa-solid fa-cubes"></i> Extracted Chunks
            </h3>
            <button onclick="closeChunksPanel()" class="text-xs text-slate-400 hover:text-white">✕</button>
          </div>
          <p class="text-[11px] text-slate-400">Document: <span id="chunkDocName" class="text-slate-200 font-mono"></span></p>
          <div id="chunksList" class="space-y-2 max-h-60 overflow-y-auto text-xs font-mono text-slate-300"></div>
        </div>

      </div>

      <!-- Column 2 & 3: Main Ingest, Queue, Findings & Audit Logs -->
      <div class="lg:col-span-2 space-y-6">

        <!-- Document Upload Card -->
        <div class="card p-6 space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-base font-semibold text-white flex items-center gap-2">
              <i class="fa-solid fa-file-arrow-up text-indigo-400"></i> Ingest Document
            </h2>
            <span class="text-xs text-slate-400">Accepts .pdf and .csv (Max 10MB)</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-xs text-slate-400 mb-1">Select File</label>
              <input id="docFile" type="file" accept=".pdf,.csv" class="w-full input-box text-xs file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer">
            </div>
            <div>
              <label class="block text-xs text-slate-400 mb-1">Document Category</label>
              <select id="docType" class="w-full input-box text-sm">
                <option value="invoice">Invoice</option>
                <option value="purchase_order">Purchase Order</option>
                <option value="contract">Contract</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs text-slate-400">Idempotency Key (Optional)</label>
              <button onclick="newIdempotencyKey()" class="text-[11px] text-indigo-400 hover:underline">Generate New Key</button>
            </div>
            <input id="idempotencyKey" type="text" class="w-full input-box text-xs font-mono" placeholder="uuid or unique client token">
          </div>

          <button onclick="handleUpload()" class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-sm font-medium transition flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20">
            <i class="fa-solid fa-cloud-arrow-up"></i> Upload & Enqueue (202 Accepted)
          </button>
        </div>

        <!-- Audit Findings Table (Day 4) -->
        <div class="card p-6 space-y-4 border-rose-500/20">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h2 class="text-base font-semibold text-white flex items-center gap-2">
                <i class="fa-solid fa-triangle-exclamation text-rose-400"></i> Audit Findings (Rules Engine)
              </h2>
              <span id="findingsCountBadge" class="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">0</span>
            </div>
            <div class="flex items-center gap-2">
              <select id="findingsFilterStatus" onchange="loadFindings()" class="input-box text-xs py-1">
                <option value="">All Statuses</option>
                <option value="open">Open</option>
                <option value="confirmed">Confirmed</option>
                <option value="dismissed">Dismissed</option>
              </select>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-300">
              <thead class="bg-slate-800/60 uppercase text-[10px] text-slate-400 tracking-wider">
                <tr>
                  <th class="py-2.5 px-3">Rule</th>
                  <th class="py-2.5 px-3">Severity</th>
                  <th class="py-2.5 px-3">Reason</th>
                  <th class="py-2.5 px-3">Status</th>
                  <th class="py-2.5 px-3">Actions</th>
                </tr>
              </thead>
              <tbody id="findingsTableBody" class="divide-y divide-slate-800">
                <tr>
                  <td colspan="5" class="py-6 text-center text-slate-500">Sign in to view audit findings</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Live Queue & Document History -->
        <div class="card p-6 space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h2 class="text-base font-semibold text-white flex items-center gap-2">
                <i class="fa-solid fa-list-check text-indigo-400"></i> Uploaded Documents & Chunks
              </h2>
              <span id="docCountBadge" class="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">0</span>
            </div>
            <div class="flex items-center gap-3">
              <label class="flex items-center gap-1.5 text-xs text-slate-400 cursor-pointer">
                <input id="autoRefreshCheckbox" type="checkbox" checked class="rounded bg-slate-900 border-slate-700 text-indigo-600 focus:ring-0">
                Auto-poll (2s)
              </label>
              <button onclick="refreshData()" class="p-1.5 text-slate-400 hover:text-white rounded hover:bg-slate-700 transition" title="Refresh Now">
                <i class="fa-solid fa-rotate"></i>
              </button>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-300">
              <thead class="bg-slate-800/60 uppercase text-[10px] text-slate-400 tracking-wider">
                <tr>
                  <th class="py-2.5 px-3">Filename</th>
                  <th class="py-2.5 px-3">Type</th>
                  <th class="py-2.5 px-3">Status</th>
                  <th class="py-2.5 px-3">Created</th>
                  <th class="py-2.5 px-3">Chunks</th>
                </tr>
              </thead>
              <tbody id="documentsTableBody" class="divide-y divide-slate-800">
                <tr>
                  <td colspan="5" class="py-6 text-center text-slate-500">Sign in to view your documents</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Extracted Invoices Table -->
        <div class="card p-6 space-y-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h2 class="text-base font-semibold text-white flex items-center gap-2">
                <i class="fa-solid fa-file-invoice-dollar text-emerald-400"></i> Extracted Invoices
              </h2>
              <span id="invoiceCountBadge" class="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">0</span>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-300">
              <thead class="bg-slate-800/60 uppercase text-[10px] text-slate-400 tracking-wider">
                <tr>
                  <th class="py-2.5 px-3">Invoice #</th>
                  <th class="py-2.5 px-3">Vendor</th>
                  <th class="py-2.5 px-3">Amount</th>
                  <th class="py-2.5 px-3">Date</th>
                  <th class="py-2.5 px-3">GSTIN</th>
                </tr>
              </thead>
              <tbody id="invoicesTableBody" class="divide-y divide-slate-800">
                <tr>
                  <td colspan="5" class="py-6 text-center text-slate-500">No invoices extracted yet</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Append-Only Audit Log Trail (Day 4) -->
        <div class="card p-6 space-y-4 border-slate-700">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h2 class="text-base font-semibold text-white flex items-center gap-2">
                <i class="fa-solid fa-fingerprint text-indigo-400"></i> Immutable Audit Trail
              </h2>
              <span id="auditCountBadge" class="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">0</span>
            </div>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-300">
              <thead class="bg-slate-800/60 uppercase text-[10px] text-slate-400 tracking-wider">
                <tr>
                  <th class="py-2.5 px-3">Action</th>
                  <th class="py-2.5 px-3">Entity</th>
                  <th class="py-2.5 px-3">Entity ID</th>
                  <th class="py-2.5 px-3">Timestamp</th>
                </tr>
              </thead>
              <tbody id="auditTableBody" class="divide-y divide-slate-800">
                <tr>
                  <td colspan="4" class="py-6 text-center text-slate-500">No audit actions recorded yet</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- API Live Console Log -->
        <div class="card p-4 space-y-2">
          <div class="flex items-center justify-between text-xs text-slate-400">
            <span><i class="fa-solid fa-terminal mr-1 text-slate-500"></i> Last API Response</span>
            <button onclick="document.getElementById('apiResponseView').textContent = 'No requests sent yet.'" class="hover:text-white text-[10px]">Clear</button>
          </div>
          <pre id="apiResponseView" class="p-3 bg-slate-950 rounded text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-48 border border-slate-800">No requests sent yet.</pre>
        </div>

      </div>

    </div>

  </div>

  <script>
    let token = localStorage.getItem("auditflow_token") || "";
    let currentUser = null;

    function logResponse(status, data) {
      const viewer = document.getElementById("apiResponseView");
      viewer.textContent = `Status: ${status}\\n` + JSON.stringify(data, null, 2);
    }

    async function checkHealth() {
      try {
        const res = await fetch("/health");
        const data = await res.json();
        const dot = document.getElementById("healthDot");
        const text = document.getElementById("healthText");
        if (res.ok && data.status === "healthy") {
          dot.className = "w-2 h-2 rounded-full bg-emerald-400";
          text.textContent = "API & DB Online";
        } else {
          dot.className = "w-2 h-2 rounded-full bg-rose-400";
          text.textContent = "Degraded";
        }
      } catch (err) {
        document.getElementById("healthDot").className = "w-2 h-2 rounded-full bg-rose-500";
        document.getElementById("healthText").textContent = "Offline";
      }
    }

    function switchAuthTab(tab) {
      if (tab === "login") {
        document.getElementById("loginForm").classList.remove("hidden");
        document.getElementById("registerForm").classList.add("hidden");
        document.getElementById("tabBtnLogin").className = "pb-2 px-4 border-b-2 border-indigo-500 text-indigo-400";
        document.getElementById("tabBtnRegister").className = "pb-2 px-4 border-b-2 border-transparent text-slate-400 hover:text-slate-200";
      } else {
        document.getElementById("loginForm").classList.add("hidden");
        document.getElementById("registerForm").classList.remove("hidden");
        document.getElementById("tabBtnLogin").className = "pb-2 px-4 border-b-2 border-transparent text-slate-400 hover:text-slate-200";
        document.getElementById("tabBtnRegister").className = "pb-2 px-4 border-b-2 border-indigo-500 text-indigo-400";
      }
    }

    async function handleLogin() {
      const email = document.getElementById("loginEmail").value.trim();
      const password = document.getElementById("loginPassword").value;
      if (!email || !password) return alert("Please fill email and password");

      try {
        const res = await fetch("/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        logResponse(res.status, data);

        if (res.ok) {
          setSession(data.access_token);
        } else {
          alert(data.detail || "Authentication failed");
        }
      } catch (err) {
        alert("Login request failed: " + err);
      }
    }

    async function handleRegister() {
      const tenant_name = document.getElementById("regTenant").value.trim();
      const email = document.getElementById("regEmail").value.trim();
      const password = document.getElementById("regPassword").value;
      if (!tenant_name || !email || !password) return alert("Please fill all fields");

      try {
        const res = await fetch("/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tenant_name, email, password, role: "admin" })
        });
        const data = await res.json();
        logResponse(res.status, data);

        if (res.ok) {
          setSession(data.access_token);
          alert("Organization created and logged in!");
        } else {
          alert(data.detail || "Registration failed");
        }
      } catch (err) {
        alert("Registration request failed: " + err);
      }
    }

    async function generateRandomTenant() {
      const rand = Math.floor(Math.random() * 90000) + 10000;
      const tenant_name = "Org " + rand;
      const email = `auditor_${rand}@tenant.com`;
      const password = "Password" + rand + "!";

      document.getElementById("regTenant").value = tenant_name;
      document.getElementById("regEmail").value = email;
      document.getElementById("regPassword").value = password;
      switchAuthTab("register");
      await handleRegister();
    }

    async function setSession(newToken) {
      token = newToken;
      localStorage.setItem("auditflow_token", token);
      await fetchUserContext();
      refreshData();
    }

    function logout() {
      token = "";
      currentUser = null;
      localStorage.removeItem("auditflow_token");
      updateAuthUI();
      document.getElementById("documentsTableBody").innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-500">Sign in to view your documents</td></tr>`;
      document.getElementById("invoicesTableBody").innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-500">No invoices extracted yet</td></tr>`;
      document.getElementById("findingsTableBody").innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-500">Sign in to view audit findings</td></tr>`;
      document.getElementById("auditTableBody").innerHTML = `<tr><td colspan="4" class="py-6 text-center text-slate-500">No audit actions recorded yet</td></tr>`;
      document.getElementById("docCountBadge").textContent = "0";
      document.getElementById("invoiceCountBadge").textContent = "0";
      document.getElementById("findingsCountBadge").textContent = "0";
      document.getElementById("auditCountBadge").textContent = "0";
      closeChunksPanel();
    }

    async function fetchUserContext() {
      if (!token) return updateAuthUI();
      try {
        const res = await fetch("/auth/me", {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          currentUser = await res.json();
          updateAuthUI();
        } else {
          logout();
        }
      } catch (err) {
        logout();
      }
    }

    function updateAuthUI() {
      const badge = document.getElementById("authStatusBadge");
      const badgeText = document.getElementById("authStatusText");
      const banner = document.getElementById("activeSessionBanner");

      if (currentUser) {
        badge.className = "flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs border border-emerald-500/20";
        badgeText.textContent = "Authenticated";
        banner.classList.remove("hidden");
        document.getElementById("lblTenantName").textContent = currentUser.email.split("@")[1] || "Tenant";
        document.getElementById("lblTenantId").textContent = `(${currentUser.tenant_id})`;
        document.getElementById("lblUserEmail").textContent = currentUser.email;
        document.getElementById("lblUserRole").textContent = currentUser.role;
      } else {
        badge.className = "flex items-center gap-2 px-3 py-1.5 rounded-full bg-rose-500/10 text-rose-400 text-xs border border-rose-500/20";
        badgeText.textContent = "Not Authenticated";
        banner.classList.add("hidden");
      }
    }

    function newIdempotencyKey() {
      document.getElementById("idempotencyKey").value = 'idem-' + Math.random().toString(36).substring(2, 12);
    }

    async function handleUpload() {
      if (!token) return alert("Please authenticate first.");
      const fileInput = document.getElementById("docFile");
      if (!fileInput.files || fileInput.files.length === 0) return alert("Please select a file to upload.");

      const file = fileInput.files[0];
      const docType = document.getElementById("docType").value;
      const idempotencyKey = document.getElementById("idempotencyKey").value.trim();

      const formData = new FormData();
      formData.append("file", file);
      formData.append("doc_type", docType);

      const headers = { "Authorization": `Bearer ${token}` };
      if (idempotencyKey) {
        headers["Idempotency-Key"] = idempotencyKey;
      }

      try {
        const res = await fetch("/documents", {
          method: "POST",
          headers: headers,
          body: formData
        });
        const data = await res.json();
        logResponse(res.status, data);

        if (res.ok) {
          fileInput.value = "";
          refreshData();
        } else {
          alert(data.detail || "Upload rejected.");
        }
      } catch (err) {
        alert("Upload error: " + err);
      }
    }

    async function seedTestDuplicateInvoice() {
      if (!token) return alert("Please authenticate first.");
      const csvData = "vendor,invoice_number,date,amount,gstin\\nSharma Traders,INV-1042-SEED,2026-08-12,118000.00,07AAAAA0000A1Z5";
      const blob = new Blob([csvData], { type: "text/csv" });
      const file = new File([blob], "invoice_seeded_dup.csv", { type: "text/csv" });

      const formData = new FormData();
      formData.append("file", file);
      formData.append("doc_type", "invoice");

      try {
        const res = await fetch("/documents", {
          method: "POST",
          headers: { "Authorization": `Bearer ${token}` },
          body: formData
        });
        const data = await res.json();
        logResponse(res.status, data);
        if (res.ok) {
          alert("Seeded duplicate invoice enqueued! The rules engine will flag it.");
          setTimeout(refreshData, 1500);
        }
      } catch (err) {
        alert("Seed failed: " + err);
      }
    }

    async function refreshData() {
      await loadDocuments();
      await loadInvoices();
      await loadFindings();
      await loadAuditLogs();
    }

    async function loadDocuments() {
      if (!token) return;
      try {
        const res = await fetch("/documents", {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) return;
        const docs = await res.json();
        document.getElementById("docCountBadge").textContent = docs.length;

        const tbody = document.getElementById("documentsTableBody");
        if (docs.length === 0) {
          tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-500">No documents uploaded yet for this tenant.</td></tr>`;
          return;
        }

        tbody.innerHTML = docs.map(d => {
          let badgeColor = "bg-slate-700 text-slate-300";
          if (d.status === "queued") badgeColor = "bg-amber-500/20 text-amber-300 border border-amber-500/30";
          else if (d.status === "processing") badgeColor = "bg-blue-500/20 text-blue-300 border border-blue-500/30 animate-pulse";
          else if (d.status === "done") badgeColor = "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
          else if (d.status === "failed") badgeColor = "bg-rose-500/20 text-rose-300 border border-rose-500/30";

          return `
            <tr class="hover:bg-slate-800/40">
              <td class="py-2.5 px-3 font-medium text-slate-200">${escapeHtml(d.filename)}</td>
              <td class="py-2.5 px-3 uppercase text-[10px] text-slate-400">${d.type}</td>
              <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[10px] uppercase font-semibold ${badgeColor}">${d.status}</span></td>
              <td class="py-2.5 px-3 text-slate-400">${new Date(d.created_at).toLocaleTimeString()}</td>
              <td class="py-2.5 px-3">
                <button onclick="viewChunks('${d.id}', '${escapeHtml(d.filename)}')" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-indigo-400 rounded text-[11px] transition">
                  <i class="fa-solid fa-eye mr-1"></i> Chunks
                </button>
              </td>
            </tr>
          `;
        }).join("");
      } catch (err) {
        console.error("Failed to load documents", err);
      }
    }

    async function loadInvoices() {
      if (!token) return;
      try {
        const res = await fetch("/invoices", {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) return;
        const invoices = await res.json();
        document.getElementById("invoiceCountBadge").textContent = invoices.length;

        const tbody = document.getElementById("invoicesTableBody");
        if (invoices.length === 0) {
          tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-500">No invoices extracted yet.</td></tr>`;
          return;
        }

        tbody.innerHTML = invoices.map(i => `
          <tr class="hover:bg-slate-800/40">
            <td class="py-2.5 px-3 font-mono font-medium text-indigo-300">${escapeHtml(i.invoice_number)}</td>
            <td class="py-2.5 px-3 font-medium text-slate-200">${escapeHtml(i.vendor_name)}</td>
            <td class="py-2.5 px-3 text-emerald-400 font-semibold font-mono">₹${Number(i.total_amount).toLocaleString()}</td>
            <td class="py-2.5 px-3 text-slate-400">${i.invoice_date || "—"}</td>
            <td class="py-2.5 px-3 font-mono text-[11px] text-slate-400">${i.vendor_gstin || "—"}</td>
          </tr>
        `).join("");
      } catch (err) {
        console.error("Failed to load invoices", err);
      }
    }

    async function loadFindings() {
      if (!token) return;
      const statusFilter = document.getElementById("findingsFilterStatus").value;
      let url = "/findings";
      if (statusFilter) url += `?status=${statusFilter}`;

      try {
        const res = await fetch(url, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) return;
        const findings = await res.json();
        document.getElementById("findingsCountBadge").textContent = findings.length;

        const tbody = document.getElementById("findingsTableBody");
        if (findings.length === 0) {
          tbody.innerHTML = `<tr><td colspan="5" class="py-6 text-center text-slate-500">No findings reported for this filter.</td></tr>`;
          return;
        }

        tbody.innerHTML = findings.map(f => {
          let sevColor = "bg-slate-700 text-slate-300";
          if (f.severity === "critical") sevColor = "bg-rose-600/30 text-rose-300 border border-rose-500/40 font-bold";
          else if (f.severity === "high") sevColor = "bg-orange-500/20 text-orange-300 border border-orange-500/30";
          else if (f.severity === "medium") sevColor = "bg-amber-500/20 text-amber-300 border border-amber-500/30";

          let statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-slate-800 text-slate-300 border border-slate-700">${f.status}</span>`;
          if (f.status === "open") statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">OPEN</span>`;
          else if (f.status === "confirmed") statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">CONFIRMED</span>`;
          else if (f.status === "dismissed") statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] uppercase font-semibold bg-slate-700 text-slate-400">DISMISSED</span>`;

          const actions = f.status === "open" ? `
            <div class="flex items-center gap-1.5">
              <button onclick="updateFinding('${f.id}', 'confirmed')" class="px-2 py-0.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-medium transition" title="Confirm Finding">
                Confirm
              </button>
              <button onclick="updateFinding('${f.id}', 'dismissed')" class="px-2 py-0.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-[10px] font-medium transition" title="Dismiss Finding">
                Dismiss
              </button>
            </div>
          ` : `<span class="text-[10px] text-slate-500 italic">Resolved</span>`;

          return `
            <tr class="hover:bg-slate-800/40">
              <td class="py-2.5 px-3 font-mono font-medium text-indigo-300">${escapeHtml(f.rule)}</td>
              <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[10px] uppercase ${sevColor}">${f.severity}</span></td>
              <td class="py-2.5 px-3 text-slate-200 max-w-xs text-xs">${escapeHtml(f.reason)}</td>
              <td class="py-2.5 px-3">${statusBadge}</td>
              <td class="py-2.5 px-3">${actions}</td>
            </tr>
          `;
        }).join("");
      } catch (err) {
        console.error("Failed to load findings", err);
      }
    }

    async function updateFinding(findingId, newStatus) {
      if (!token) return;
      const notes = prompt(`Enter notes for marking finding as ${newStatus}:`, `Verified by auditor on ${new Date().toLocaleDateString()}`);
      if (notes === null) return;

      try {
        const res = await fetch(`/findings/${findingId}`, {
          method: "PATCH",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ status: newStatus, notes: notes })
        });
        const data = await res.json();
        logResponse(res.status, data);
        if (res.ok) {
          refreshData();
        } else {
          alert(data.detail || "Update failed.");
        }
      } catch (err) {
        alert("Action error: " + err);
      }
    }

    async function loadAuditLogs() {
      if (!token) return;
      try {
        const res = await fetch("/audit-logs", {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) return;
        const logs = await res.json();
        document.getElementById("auditCountBadge").textContent = logs.length;

        const tbody = document.getElementById("auditTableBody");
        if (logs.length === 0) {
          tbody.innerHTML = `<tr><td colspan="4" class="py-6 text-center text-slate-500">No audit actions recorded yet.</td></tr>`;
          return;
        }

        tbody.innerHTML = logs.map(l => `
          <tr class="hover:bg-slate-800/40">
            <td class="py-2 px-3 font-mono font-medium text-emerald-400">${escapeHtml(l.action)}</td>
            <td class="py-2 px-3 uppercase text-[10px] text-slate-400">${escapeHtml(l.entity)}</td>
            <td class="py-2 px-3 font-mono text-[10px] text-slate-500" title="${l.entity_id}">${l.entity_id.substring(0, 8)}...</td>
            <td class="py-2 px-3 text-slate-400 text-[11px]">${new Date(l.created_at).toLocaleTimeString()}</td>
          </tr>
        `).join("");
      } catch (err) {
        console.error("Failed to load audit logs", err);
      }
    }

    async function viewChunks(docId, filename) {
      if (!token) return;
      try {
        const res = await fetch(`/documents/${docId}/chunks`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) return alert("Failed to fetch chunks.");
        const chunks = await res.json();

        document.getElementById("chunkDocName").textContent = filename;
        const listDiv = document.getElementById("chunksList");

        if (chunks.length === 0) {
          listDiv.innerHTML = `<div class="p-3 bg-slate-900 rounded text-slate-500 text-center">No chunks generated yet.</div>`;
        } else {
          listDiv.innerHTML = chunks.map(c => `
            <div class="p-2.5 bg-slate-900 rounded border border-slate-800 space-y-1">
              <div class="flex items-center justify-between text-[10px] text-indigo-400 font-semibold">
                <span>Chunk #${c.chunk_index}</span>
                <span>Page ${c.page || 1} • pgvector (1536d)</span>
              </div>
              <p class="text-slate-300 text-[11px] leading-relaxed break-words">${escapeHtml(c.text)}</p>
            </div>
          `).join("");
        }

        document.getElementById("chunksCard").classList.remove("hidden");
      } catch (err) {
        alert("Error fetching chunks: " + err);
      }
    }

    function closeChunksPanel() {
      document.getElementById("chunksCard").classList.add("hidden");
    }

    function escapeHtml(str) {
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // Initialize
    checkHealth();
    newIdempotencyKey();
    fetchUserContext();

    // Polling setup
    setInterval(() => {
      checkHealth();
      const autoRefresh = document.getElementById("autoRefreshCheckbox").checked;
      if (autoRefresh && token) {
        refreshData();
      }
    }, 2000);
  </script>
</body>
</html>
"""


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def get_testing_dashboard() -> HTMLResponse:
    """Serve the single-page testing dashboard."""
    return HTMLResponse(content=HTML_CONTENT)
