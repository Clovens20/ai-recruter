import { useState } from "react";
import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";

export const Login = ({ onLogin, loading, error }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    await onLogin({ email, password });
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center px-4">
      <div className="w-full max-w-md rounded-xl bg-[#0F0F0F] border border-white/[0.08] p-6 space-y-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#2563EB] flex items-center justify-center ai-glow">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-heading text-xl font-bold text-white">Konekte Recruiter</h1>
            <p className="text-xs text-[#94A3B8]">Connexion securisee</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
              Email
            </Label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@konektegroup.com"
              className="bg-[#050505] border-white/[0.08] text-[#F8FAFC]"
              required
            />
          </div>

          <div className="space-y-2">
            <Label className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
              Mot de passe
            </Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="********"
              className="bg-[#050505] border-white/[0.08] text-[#F8FAFC]"
              required
            />
          </div>

          {error ? <p className="text-sm text-red-400">{error}</p> : null}

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-[#2563EB] hover:bg-[#1D4ED8] text-white"
          >
            {loading ? "Connexion..." : "Se connecter"}
          </Button>
        </form>

        <p className="flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-center text-[11px] text-[#64748B]">
          <Link to="/legal/privacy" className="text-blue-500 hover:text-blue-400 hover:underline">
            Politik konfidansyalite
          </Link>
          <span className="text-[#475569]">·</span>
          <Link to="/legal/terms" className="text-blue-500 hover:text-blue-400 hover:underline">
            Kondisyon itilizasyon
          </Link>
          <span className="text-[#475569]">·</span>
          <Link to="/legal/cookies" className="text-blue-500 hover:text-blue-400 hover:underline">
            Politik sou kòki
          </Link>
        </p>
      </div>
    </div>
  );
};
