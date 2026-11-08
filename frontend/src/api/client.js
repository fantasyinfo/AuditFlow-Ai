const API_BASE =
  typeof window !== "undefined" && (window.location.port === "3000" || window.location.port === "5173")
    ? "http://localhost:8000"
    : "";

function getAuthHeader() {
  const token = localStorage.getItem("auditflow_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(url, options = {}) {
  const headers = {
    ...getAuthHeader(),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type");
  const isJson = contentType && contentType.includes("application/json");
  let data = null;
  try {
    const text = await response.text();
    if (text && text.trim()) {
      data = isJson ? JSON.parse(text) : text;
    }
  } catch (parseErr) {
    data = null;
  }

  if (!response.ok) {
    const errorMsg = (data && data.detail) || `Request failed with status ${response.status}`;
    const err = new Error(errorMsg);
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data;
}

export const api = {
  health: {
    check: () => request("/health"),
  },

  auth: {
    login: (email, password) =>
      request("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      }),

    register: (tenant_name, email, password, role = "admin") =>
      request("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tenant_name, email, password, role }),
      }),

    getMe: () => request("/auth/me"),
  },

  documents: {
    upload: (file, docType = "invoice", idempotencyKey = "", projectId = "") => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("doc_type", docType);
      if (projectId) {
        formData.append("project_id", projectId);
      }

      const headers = {};
      if (idempotencyKey) {
        headers["Idempotency-Key"] = idempotencyKey;
      }

      return request("/documents", {
        method: "POST",
        headers,
        body: formData,
      });
    },

    list: (status = "", limit = 50) => {
      let q = `/documents?limit=${limit}`;
      if (status) q += `&status=${status}`;
      return request(q);
    },

    get: (id) => request(`/documents/${id}`),

    getChunks: (id) => request(`/documents/${id}/chunks`),

    delete: (id) =>
      request(`/documents/${id}`, {
        method: "DELETE",
      }),
  },

  invoices: {
    list: (limit = 50, documentId = "") =>
      request(`/invoices?limit=${limit}${documentId ? `&document_id=${documentId}` : ""}`),
    get: (id) => request(`/invoices/${id}`),
    delete: (id) =>
      request(`/invoices/${id}`, {
        method: "DELETE",
      }),
  },

  findings: {
    list: (status = "", rule = "", limit = 50) => {
      const params = new URLSearchParams();
      if (status) params.append("status", status);
      if (rule) params.append("rule", rule);
      params.append("limit", limit.toString());
      return request(`/findings?${params.toString()}`);
    },

    get: (id) => request(`/findings/${id}`),

    update: (id, newStatus, notes = "") =>
      request(`/findings/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus, notes }),
      }),

    delete: (id) =>
      request(`/findings/${id}`, {
        method: "DELETE",
      }),
  },

  assistant: {
    ask: (query) =>
      request("/agent/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      }),
  },

  auditLogs: {
    list: (limit = 50) => request(`/audit-logs?limit=${limit}`),
  },

  rules: {
    list: () => request("/rules"),
    listCustom: () => request("/rules/custom"),
    createCustom: (data) =>
      request("/rules/custom", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),
    updateCustom: (id, data) =>
      request(`/rules/custom/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),
    deleteCustom: (id) =>
      request(`/rules/custom/${id}`, {
        method: "DELETE",
      }),
  },

  projects: {
    list: () => request("/projects"),
    get: (id) => request(`/projects/${id}`),
    create: (data) =>
      request("/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),
    update: (id, data) =>
      request(`/projects/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),
    delete: (id) =>
      request(`/projects/${id}`, {
        method: "DELETE",
      }),
    getReconciliation: (id) => request(`/projects/${id}/reconciliation`),
    recordPayment: (projectId, invoiceId, data) =>
      request(`/projects/${projectId}/invoices/${invoiceId}/payments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }),
    linkInvoice: (projectId, invoiceId) =>
      request(`/projects/${projectId}/link-invoice/${invoiceId}`, {
        method: "POST",
      }),
    linkDocument: (projectId, documentId) =>
      request(`/projects/${projectId}/link-document/${documentId}`, {
        method: "POST",
      }),
  },

  system: {
    getAiStatus: () => request("/system/ai-status"),
    configureAi: (geminiApiKey, model = "gemini-2.0-flash") =>
      request("/system/ai-config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gemini_api_key: geminiApiKey, model }),
      }),
  },
};

