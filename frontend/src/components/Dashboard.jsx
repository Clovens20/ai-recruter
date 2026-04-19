import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { StatsCards } from "./StatsCards";
import { LeadsTable } from "./LeadsTable";
import { Button } from "../components/ui/button";
import { UserSearch, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import api from "../lib/api";

export const Dashboard = () => {
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [agentRunning, setAgentRunning] = useState(false);
  const [showOnlyReplied, setShowOnlyReplied] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [leadsRes, statsRes] = await Promise.all([
        api.get("/leads"),
        api.get("/leads/stats"),
      ]);
      setLeads(leadsRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error("Error fetching data:", err);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleStatusChange = async (id, status) => {
    try {
      await api.patch(`/leads/${id}/status`, { status });
      await fetchData();
    } catch (err) {
      console.error("Error updating status:", err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/leads/${id}`);
      await fetchData();
    } catch (err) {
      console.error("Error deleting lead:", err);
    }
  };

  const handleRegenerate = async (id) => {
    try {
      const res = await api.post(`/leads/${id}/regenerate-message`);
      // Update the lead in the local state
      setLeads((prev) =>
        prev.map((l) =>
          l.id === id ? { ...l, generated_message: res.data.message } : l
        )
      );
    } catch (err) {
      console.error("Error regenerating message:", err);
    }
  };

  const handleRunAgent = async () => {
    setAgentRunning(true);
    try {
      const res = await api.post("/agent/run", {
        dry_run: false,
        max_profiles: 25,
        discover_youtube: true,
        discover_tiktok: true,
        discover_instagram: true,
        discover_facebook: true,
        youtube_max_results: 20,
      });
      await fetchData();
      window.alert(res.data?.summary || "Agent lanse ak siksè.");
    } catch (err) {
      console.error("Error running agent:", err);
      window.alert(err?.response?.data?.detail || "Erreur lors du lancement de l'agent.");
    } finally {
      setAgentRunning(false);
    }
  };

  const displayedLeads = showOnlyReplied
    ? leads.filter((lead) => lead.status === "replied")
    : leads;

  return (
    <div data-testid="dashboard-page">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8"
      >
        <div>
          <h1 className="font-heading text-4xl sm:text-5xl font-black tracking-tighter text-white">
            Dashboard
          </h1>
          <p className="text-base text-[#94A3B8] mt-1">
            Gerez vos leads educateurs et createurs de contenu
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            data-testid="toggle-replied-btn"
            onClick={() => setShowOnlyReplied((prev) => !prev)}
            className="bg-white/10 hover:bg-white/20 text-white font-medium"
          >
            {showOnlyReplied ? "Tous les leads" : "Messages recus"}
          </Button>
          <Button
            data-testid="goto-agent-results-btn"
            onClick={() => navigate("/agents?view=results")}
            className="bg-white/10 hover:bg-white/20 text-white font-medium"
          >
            Suivi agent
          </Button>
          <Button
            data-testid="run-agent-btn"
            onClick={handleRunAgent}
            disabled={agentRunning}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            {agentRunning ? "Agent ap travay..." : "Lanse Agent"}
          </Button>
          <Button
            data-testid="goto-analyze-btn"
            onClick={() => navigate("/analyze")}
            className="bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-medium ai-glow"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Analyser un Profil
          </Button>
        </div>
      </motion.div>

      {/* Stats */}
      <div className="mb-8">
        <StatsCards stats={stats} />
      </div>

      {/* Leads Table */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.15 }}
      >
        <div className="flex items-center gap-2 mb-4">
          <UserSearch className="w-4 h-4 text-[#2563EB]" />
          <h3 className="font-heading text-lg font-semibold text-white">
            {showOnlyReplied ? "Personnes ayant repondu" : "Leads Recrutes"}
          </h3>
          <span className="text-sm text-[#64748B]">({displayedLeads.length})</span>
        </div>
        <LeadsTable
          leads={displayedLeads}
          onStatusChange={handleStatusChange}
          onDelete={handleDelete}
          onRegenerate={handleRegenerate}
          loading={loading}
        />
      </motion.div>
    </div>
  );
};
