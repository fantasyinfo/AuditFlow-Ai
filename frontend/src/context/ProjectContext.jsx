import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { api } from "../api/client";
import { useAuth } from "./AuthContext";

const ProjectContext = createContext(null);

export function ProjectProvider({ children }) {
  const { currentUser, token } = useAuth();
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(
    () => localStorage.getItem("auditflow_selected_project") || ""
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchProjects = useCallback(async () => {
    const activeToken = token || localStorage.getItem("auditflow_token");
    if (!activeToken) {
      setProjects([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.projects.list();
      const list = res?.projects || [];
      setProjects(list);

      setSelectedProjectId((prevId) => {
        if (list.length > 0 && (!prevId || !list.some((p) => p.id === prevId))) {
          localStorage.setItem("auditflow_selected_project", list[0].id);
          return list[0].id;
        }
        return prevId;
      });
    } catch (err) {
      console.error("Failed to load projects:", err);
      setError(err.message || "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, [token, currentUser]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const selectProject = (id) => {
    setSelectedProjectId(id);
    if (id) {
      localStorage.setItem("auditflow_selected_project", id);
    } else {
      localStorage.removeItem("auditflow_selected_project");
    }
  };

  const selectedProject = projects.find((p) => p.id === selectedProjectId) || null;

  return (
    <ProjectContext.Provider
      value={{
        projects,
        selectedProject,
        selectedProjectId,
        selectProject,
        refreshProjects: fetchProjects,
        loading,
        error,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const ctx = useContext(ProjectContext);
  if (!ctx) {
    throw new Error("useProject must be used within a ProjectProvider");
  }
  return ctx;
}

