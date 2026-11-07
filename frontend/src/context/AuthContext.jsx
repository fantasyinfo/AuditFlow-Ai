import React, { createContext, useContext, useState, useEffect } from "react";
import { api } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("auditflow_token") || "");
  const [currentUser, setCurrentUser] = useState(null);
  const [tenant, setTenant] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchProfile = async (authToken) => {
    if (!authToken) {
      setCurrentUser(null);
      setTenant(null);
      setIsLoading(false);
      return;
    }

    try {
      const user = await api.auth.getMe();
      setCurrentUser(user);
      setTenant({
        id: user.tenant_id,
        name: user.tenant_name || "Primary Tenant",
      });
    } catch (err) {
      console.error("Session expired or invalid token:", err);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchProfile(token);
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    setIsLoading(true);
    try {
      const res = await api.auth.login(email, password);
      localStorage.setItem("auditflow_token", res.access_token);
      setToken(res.access_token);
      await fetchProfile(res.access_token);
      return res;
    } catch (err) {
      setIsLoading(false);
      throw err;
    }
  };

  const register = async (tenantName, email, password) => {
    setIsLoading(true);
    try {
      const res = await api.auth.register(tenantName, email, password, "admin");
      localStorage.setItem("auditflow_token", res.access_token);
      setToken(res.access_token);
      await fetchProfile(res.access_token);
      return res;
    } catch (err) {
      setIsLoading(false);
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem("auditflow_token");
    setToken("");
    setCurrentUser(null);
    setTenant(null);
  };

  const createRandomTenant = async () => {
    const rand = Math.floor(Math.random() * 90000) + 10000;
    const tName = `Enterprise Corp ${rand}`;
    const email = `controller_${rand}@auditflow.ai`;
    const password = `SecurePass${rand}!`;
    return register(tName, email, password);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        currentUser,
        tenant,
        isAuthenticated: !!token && !!currentUser,
        isLoading,
        login,
        register,
        logout,
        createRandomTenant,
        refreshProfile: () => fetchProfile(token),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

