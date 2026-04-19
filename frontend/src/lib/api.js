import axios from "axios";

/** Base du backend sans /api final (ex. https://xxx.koyeb.app). CRA: REACT_APP_API_URL dans frontend/.env */
function apiBaseURL() {
  const u = (process.env.REACT_APP_API_URL || "").trim();
  if (!u) return "/api";
  const clean = u.replace(/\/+$/, "");
  return clean.endsWith("/api") ? clean : `${clean}/api`;
}

const api = axios.create({
  baseURL: apiBaseURL(),
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("auth_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export const fetchPublicHealth = () => api.get("/health").then((r) => r.data);
export const fetchSupabaseHealth = () => api.get("/health/supabase").then((r) => r.data);

export const searchProfiles = (category, platforms, maxResults = 20) =>
  api.post("/agent/search", { category, platforms, max_results: maxResults }).then((r) => r.data);

export const analyzeProfiles = (profiles) =>
  api.post("/agent/analyze", { profiles }).then((r) => r.data);

export const sendAgentRecruitmentEmail = (profileId, profile, dryRun = false) =>
  api.post("/agent/send-email", { profile_id: profileId, profile, dry_run: dryRun }).then((r) => r.data);

export const getAgentStatus = () => api.get("/agent/status").then((r) => r.data);

export default api;
