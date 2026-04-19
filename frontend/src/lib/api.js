import axios from "axios";

const api = axios.create({
  baseURL: "/api",
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

/** Sante backend + presence variables Supabase (pas besoin d’etre connecte pour lire ok/env). */
export const fetchPublicHealth = () => api.get("/health").then((r) => r.data);

/** Test GET leads sur Supabase — utile si 503 sur /leads (auth requise). */
export const fetchSupabaseHealth = () => api.get("/health/supabase").then((r) => r.data);

/** Agent milti-platfòm (YouTube + Apify TikTok / Instagram / Facebook selon backend). */
export const searchProfiles = (category, platforms, maxResults = 20) =>
  api
    .post("/agent/search", {
      category,
      platforms,
      max_results: maxResults,
    })
    .then((r) => r.data);

/** Analiz kreyòl, filtre score > 70, anrejistre leads (si Supabase OK). */
export const analyzeProfiles = (profiles) =>
  api.post("/agent/analyze", { profiles }).then((r) => r.data);

/** Imèl rekritman (Resend); mete dryRun=true pou previzyalizasyon san voye. */
export const sendAgentRecruitmentEmail = (profileId, profile, dryRun = false) =>
  api
    .post("/agent/send-email", {
      profile_id: profileId,
      profile,
      dry_run: dryRun,
    })
    .then((r) => r.data);

export const getAgentStatus = () => api.get("/agent/status").then((r) => r.data);

export default api;
