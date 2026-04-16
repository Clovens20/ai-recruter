import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { StatsCards } from "./StatsCards";
import { LeadsTable } from "./LeadsTable";
import { Button } from "../components/ui/button";
import { UserSearch, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const Dashboard = () => {
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [leadsRes, statsRes] = await Promise.all([
        axios.get(`${API}/leads`),
        axios.get(`${API}/leads/stats`),
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
      await axios.patch(`${API}/leads/${id}/status`, { status });
      await fetchData();
    } catch (err) {
      console.error("Error updating status:", err);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/leads/${id}`);
      await fetchData();
    } catch (err) {
      console.error("Error deleting lead:", err);
    }
  };

  const handleRegenerate = async (id) => {
    try {
      const res = await axios.post(`${API}/leads/${id}/regenerate-message`);
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
        <Button
          data-testid="goto-analyze-btn"
          onClick={() => navigate("/analyze")}
          className="bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-medium ai-glow"
        >
          <Sparkles className="w-4 h-4 mr-2" />
          Analyser un Profil
        </Button>
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
            Leads Recrutes
          </h3>
          <span className="text-sm text-[#64748B]">({leads.length})</span>
        </div>
        <LeadsTable
          leads={leads}
          onStatusChange={handleStatusChange}
          onDelete={handleDelete}
          onRegenerate={handleRegenerate}
          loading={loading}
        />
      </motion.div>
    </div>
  );
};
