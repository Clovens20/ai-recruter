import { useState } from "react";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Button } from "../components/ui/button";
import { Textarea } from "../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { ScoreBadge } from "./ScoreBadge";
import { StatusBadge } from "./StatusBadge";
import { PlatformBadge } from "./PlatformBadge";
import { Sparkles, ArrowLeft, Copy, Check } from "lucide-react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

export const ProfileAnalyzer = ({ onAnalyze }) => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    bio: "",
    platform: "",
    followers: "",
    content_example: "",
    email: "",
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.platform || !form.bio) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await onAnalyze({
        ...form,
        followers: parseInt(form.followers) || 0,
      });
      setResult(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleCopy = async () => {
    if (!result?.generated_message) return;
    await navigator.clipboard.writeText(result.generated_message);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const inputCls =
    "bg-[#050505] border-white/[0.08] text-[#F8FAFC] placeholder:text-[#4A5568] focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]/30";

  return (
    <div className="max-w-3xl mx-auto" data-testid="profile-analyzer">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-to-dashboard-btn"
            variant="ghost"
            size="sm"
            onClick={() => navigate("/")}
            className="text-[#94A3B8] hover:text-white hover:bg-white/[0.05]"
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" />
            Retour
          </Button>
        </div>

        <h2 className="font-heading text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
          Analyser un Profil
        </h2>
        <p className="text-sm text-[#94A3B8] mb-8">
          Entrez les informations du createur de contenu pour l'analyse IA
        </p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="rounded-xl bg-[#0F0F0F] border border-white/[0.08] p-6 space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="space-y-2">
                <Label className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
                  Nom complet
                </Label>
                <Input
                  data-testid="input-name"
                  placeholder="Ex: Jean Baptiste"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className={inputCls}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
                  Plateforme
                </Label>
                <Select
                  value={form.platform}
                  onValueChange={(val) => setForm({ ...form, platform: val })}
                >
                  <SelectTrigger
                    data-testid="input-platform"
                    className={`${inputCls} h-10`}
                  >
                    <SelectValue placeholder="Choisir..." />
                  </SelectTrigger>
                  <SelectContent className="bg-[#0F0F0F] border-white/[0.08]">
                    <SelectItem value="youtube" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">
                      YouTube
                    </SelectItem>
                    <SelectItem value="tiktok" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">
                      TikTok
                    </SelectItem>
                    <SelectItem value="facebook" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">
                      Facebook
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
                Bio
              </Label>
              <Textarea
                data-testid="input-bio"
                placeholder="Decrivez le profil du createur..."
                value={form.bio}
                onChange={(e) => setForm({ ...form, bio: e.target.value })}
                className={`${inputCls} min-h-[80px]`}
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div className="space-y-2">
                <Label className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
                  Nombre d'abonnes
                </Label>
                <Input
                  data-testid="input-followers"
                  type="number"
                  placeholder="Ex: 15000"
                  value={form.followers}
                  onChange={(e) => setForm({ ...form, followers: e.target.value })}
                  className={inputCls}
                />
              </div>

              <div className="space-y-2">
                <Label className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
                  Email
                </Label>
                <Input
                  data-testid="input-email"
                  type="email"
                  placeholder="Ex: formateur@email.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className={inputCls}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
                Exemple de contenu
              </Label>
              <Input
                data-testid="input-content"
                placeholder="Ex: Tutoriels de maths en creole"
                value={form.content_example}
                onChange={(e) =>
                  setForm({ ...form, content_example: e.target.value })
                }
                className={inputCls}
              />
            </div>
          </div>

          <Button
            data-testid="analyze-submit-btn"
            type="submit"
            disabled={loading || !form.name || !form.platform || !form.bio}
            className="w-full h-12 bg-[#2563EB] hover:bg-[#1D4ED8] text-white font-medium text-sm ai-glow disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Analyse en cours...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                Analyser avec l'IA
              </div>
            )}
          </Button>
        </form>

        {/* Results */}
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="mt-8 space-y-4"
            data-testid="analysis-results"
          >
            <h3 className="font-heading text-xl font-semibold text-white">
              Resultats de l'Analyse
            </h3>

            {/* Analysis Card */}
            <div className="rounded-xl bg-[#0F0F0F] border border-white/[0.08] p-6 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-lg font-medium text-white">{result.name}</p>
                  <p className="text-sm text-[#94A3B8]">{result.bio}</p>
                </div>
                <ScoreBadge score={result.score} />
              </div>

              <div className="flex flex-wrap gap-2">
                <PlatformBadge platform={result.platform} />
                <StatusBadge status={result.status} />
                <span className="inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium bg-white/[0.06] text-[#F8FAFC] border border-white/[0.08]">
                  {result.domain}
                </span>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${
                    result.is_educator
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-red-500/10 text-red-400 border border-red-500/20"
                  }`}
                >
                  {result.is_educator ? "Educateur" : "Non-Educateur"}
                </span>
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${
                    result.potential === "eleve"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : result.potential === "moyen"
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      : "bg-red-500/10 text-red-400 border border-red-500/20"
                  }`}
                >
                  Potentiel: {result.potential}
                </span>
              </div>

              {result.reasoning && (
                <p className="text-sm text-[#94A3B8] italic">{result.reasoning}</p>
              )}
            </div>

            {/* Generated Message */}
            <div className="rounded-xl bg-[#0F0F0F] border border-white/[0.08] p-6 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
                  Message de Recrutement
                </p>
                <Button
                  data-testid="copy-result-message-btn"
                  variant="ghost"
                  size="sm"
                  onClick={handleCopy}
                  className="h-8 text-[#94A3B8] hover:text-white hover:bg-white/[0.05]"
                >
                  {copied ? (
                    <Check className="w-3.5 h-3.5 mr-1.5" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 mr-1.5" />
                  )}
                  {copied ? "Copie!" : "Copier"}
                </Button>
              </div>
              <p className="text-sm text-[#F8FAFC] leading-relaxed whitespace-pre-wrap">
                {result.generated_message}
              </p>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
};
