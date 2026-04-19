import { useEffect, useMemo, useState } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import api, {
  searchProfiles,
  analyzeProfiles,
  getAgentStatus,
} from "../lib/api";
import { useSearchParams } from "react-router-dom";

const VIEWS = ["work", "config", "create", "results", "search"];

const PLATFORM_OPTIONS = [
  { id: "youtube", label: "YouTube" },
  { id: "tiktok", label: "TikTok" },
  { id: "instagram", label: "Instagram" },
  { id: "facebook", label: "Facebook" },
];

const FALLBACK_CATEGORIES = [
  "Teknoloji",
  "Marketing Digital",
  "AI",
  "Finance",
  "Biznis",
  "Kreatif",
  "Sante",
  "Lang",
  "Mizik",
  "Devlopman Pèsonèl",
  "Edikasyon",
  "Travay Atizana",
  "Lòt",
];

const defaultCreate = {
  name: "",
  function_type: "recruitment_cycle",
  enabled: true,
  dry_run: false,
  max_profiles: 25,
  discover_youtube: true,
  discover_tiktok: true,
  discover_instagram: true,
  discover_facebook: true,
  youtube_max_results: 20,
};

export const AgentsCenter = () => {
  const [searchParams] = useSearchParams();
  const initialView = searchParams.get("view");
  const [view, setView] = useState(
    VIEWS.includes(initialView) ? initialView : "work"
  );
  const [agents, setAgents] = useState([]);
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);

  const formatApiError = (err) => {
    const d = err?.response?.data?.detail;
    if (d == null) return err?.message || "Erè rezo.";
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d.map((x) => (typeof x === "object" ? JSON.stringify(x) : String(x))).join(" ");
    }
    if (typeof d === "object") return JSON.stringify(d);
    return String(d);
  };
  const [createForm, setCreateForm] = useState(defaultCreate);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [configForm, setConfigForm] = useState(defaultCreate);

  const [agentApiStatus, setAgentApiStatus] = useState(null);
  const [searchCategory, setSearchCategory] = useState("Edikasyon");
  const [platformsPick, setPlatformsPick] = useState({
    youtube: true,
    tiktok: true,
    instagram: false,
    facebook: false,
  });
  const [maxSearchResults, setMaxSearchResults] = useState(10);
  const [hashtagInput, setHashtagInput] = useState("");
  const [searchHashtags, setSearchHashtags] = useState([]);
  const [discoveredProfiles, setDiscoveredProfiles] = useState([]);
  const [searchBusy, setSearchBusy] = useState(false);
  const [analyzeBusy, setAnalyzeBusy] = useState(false);
  const [createBusy, setCreateBusy] = useState(false);
  const [createFlash, setCreateFlash] = useState("");

  const selectedAgent = useMemo(
    () => agents.find((a) => a.id === selectedAgentId) || null,
    [agents, selectedAgentId]
  );

  const loadData = async (opts = { showSpinner: true }) => {
    if (opts.showSpinner) setLoading(true);
    try {
      const [agentsRes, runsRes] = await Promise.all([
        api.get("/agents"),
        api.get("/agents/runs"),
      ]);
      setAgents(agentsRes.data || []);
      setRuns(runsRes.data || []);
      if (!selectedAgentId && (agentsRes.data || []).length > 0) {
        setSelectedAgentId(agentsRes.data[0].id);
      }
    } catch (err) {
      console.error("Failed loading agents center", err);
      if (err?.response?.status !== 401) {
        window.alert(formatApiError(err));
      }
    } finally {
      if (opts.showSpinner) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (view !== "search") return;
    let cancelled = false;
    (async () => {
      try {
        const s = await getAgentStatus();
        if (!cancelled) setAgentApiStatus(s);
      } catch (e) {
        if (!cancelled) setAgentApiStatus(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [view]);

  const categoriesForSearch = agentApiStatus?.categories?.length
    ? agentApiStatus.categories
    : FALLBACK_CATEGORIES;

  const togglePlatform = (id) => {
    setPlatformsPick((p) => ({ ...p, [id]: !p[id] }));
  };

  const selectedPlatformIds = () =>
    PLATFORM_OPTIONS.filter((o) => platformsPick[o.id]).map((o) => o.id);

  const addHashtagsFromInput = () => {
    const parts = hashtagInput
      .split(/[\s,;]+/)
      .map((s) => s.trim().replace(/^#/, ""))
      .filter(Boolean);
    if (!parts.length) return;
    setSearchHashtags((prev) => {
      const seen = new Set(prev.map((x) => x.toLowerCase()));
      const next = [...prev];
      for (const p of parts) {
        const k = p.toLowerCase();
        if (seen.has(k)) continue;
        seen.add(k);
        next.push(p);
      }
      return next;
    });
    setHashtagInput("");
  };

  const applyCategoryHashtagSuggestions = () => {
    const sug = agentApiStatus?.hashtag_suggestions?.[searchCategory];
    if (!Array.isArray(sug) || !sug.length) {
      window.alert("Pa gen sijesyon hashtag pou kategori sa a (tcheke stati API).");
      return;
    }
    setSearchHashtags((prev) => {
      const seen = new Set(prev.map((x) => x.toLowerCase()));
      const next = [...prev];
      for (const p of sug) {
        const t = String(p).trim().replace(/^#/, "");
        if (!t) continue;
        const k = t.toLowerCase();
        if (seen.has(k)) continue;
        seen.add(k);
        next.push(t);
      }
      return next;
    });
  };

  const onRunMultiSearch = async () => {
    const plats = selectedPlatformIds();
    if (plats.length === 0) {
      window.alert("Chwazi omwen yon platfòm.");
      return;
    }
    setSearchBusy(true);
    try {
      const data = await searchProfiles(
        searchCategory,
        plats,
        maxSearchResults,
        searchHashtags.length ? searchHashtags : undefined
      );
      setDiscoveredProfiles(data.profiles || []);
      window.alert(`Jwenn ${data.count ?? 0} pwofil.`);
    } catch (err) {
      window.alert(formatApiError(err));
    } finally {
      setSearchBusy(false);
    }
  };

  const onRunCreoleAnalyze = async () => {
    if (!discoveredProfiles.length) {
      window.alert("Fè yon rechèch avan.");
      return;
    }
    setAnalyzeBusy(true);
    try {
      const data = await analyzeProfiles(discoveredProfiles);
      setDiscoveredProfiles(data.profiles || []);
      window.alert(`${data.count ?? 0} pwofil kenbe (kreyòl > 70). Yo anrejistre kòm lead si Supabase OK.`);
    } catch (err) {
      window.alert(formatApiError(err));
    } finally {
      setAnalyzeBusy(false);
    }
  };

  useEffect(() => {
    if (!selectedAgent) return;
    setConfigForm({
      name: selectedAgent.name || "",
      function_type: selectedAgent.function_type || "recruitment_cycle",
      enabled: Boolean(selectedAgent.enabled),
      dry_run: Boolean(selectedAgent.settings?.dry_run),
      max_profiles: Number(selectedAgent.settings?.max_profiles || 25),
      discover_youtube: Boolean(selectedAgent.settings?.discover_youtube ?? true),
      discover_tiktok: Boolean(selectedAgent.settings?.discover_tiktok ?? true),
      discover_instagram: Boolean(selectedAgent.settings?.discover_instagram ?? true),
      discover_facebook: Boolean(selectedAgent.settings?.discover_facebook ?? true),
      youtube_max_results: Number(selectedAgent.settings?.youtube_max_results || 20),
    });
  }, [selectedAgent]);

  const onCreateAgent = async (e) => {
    e.preventDefault();
    setCreateBusy(true);
    try {
      const { data } = await api.post("/agents", createForm);
      setCreateForm(defaultCreate);
      if (data?.id) {
        setAgents((prev) => {
          const rest = prev.filter((a) => a.id !== data.id);
          return [data, ...rest];
        });
        setSelectedAgentId(data.id);
      }
      void loadData({ showSpinner: false });
      setCreateFlash("Agent kreye — senkronizasyon ak baz la ap fèt an aryè.");
      window.setTimeout(() => setCreateFlash(""), 5000);
    } catch (err) {
      window.alert(formatApiError(err));
    } finally {
      setCreateBusy(false);
    }
  };

  const onSaveConfig = async (e) => {
    e.preventDefault();
    if (!selectedAgentId) return;
    try {
      await api.patch(`/agents/${selectedAgentId}`, configForm);
      await loadData({ showSpinner: false });
      window.alert("Konfigirasyon agent mete ajou.");
    } catch (err) {
      window.alert(formatApiError(err));
    }
  };

  const onDeleteAgent = async () => {
    if (!selectedAgentId) return;
    if (!window.confirm("Efase agent sa a definitivman? (Aksyon sa a pa retabli.)")) return;
    try {
      await api.delete(`/agents/${selectedAgentId}`);
      setSelectedAgentId("");
      await loadData({ showSpinner: false });
      window.alert("Agent efase.");
    } catch (err) {
      window.alert(formatApiError(err));
    }
  };

  const onRunAgent = async (agentId) => {
    try {
      const res = await api.post(`/agents/${agentId}/run`);
      await loadData({ showSpinner: false });
      window.alert(res.data?.summary || "Agent lanse.");
    } catch (err) {
      window.alert(formatApiError(err));
    }
  };

  return (
    <div className="space-y-6" data-testid="agents-center-page">
      <div>
        <h1 className="font-heading text-4xl font-black tracking-tighter text-white">Agents</h1>
        <p className="text-[#94A3B8]">Pilotage, configuration et resultats de tes agents.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button onClick={() => setView("work")} className={view === "work" ? "" : "bg-white/10 hover:bg-white/20"}>
          Consulter travaux
        </Button>
        <Button onClick={() => setView("config")} className={view === "config" ? "" : "bg-white/10 hover:bg-white/20"}>
          Configurer l'agent
        </Button>
        <Button onClick={() => setView("create")} className={view === "create" ? "" : "bg-white/10 hover:bg-white/20"}>
          Creer plusieurs agents
        </Button>
        <Button onClick={() => setView("results")} className={view === "results" ? "" : "bg-white/10 hover:bg-white/20"}>
          Voir resultats
        </Button>
        <Button
          onClick={() => setView("search")}
          className={view === "search" ? "" : "bg-emerald-600/90 hover:bg-emerald-600 text-white"}
        >
          Rechèch milti-platfòm
        </Button>
      </div>

      {loading && view !== "create" ? (
        <p className="text-[#94A3B8] text-sm">Chajman done agent yo...</p>
      ) : null}

      {view === "work" ? (
        <div className="rounded-xl bg-[#0F0F0F] border border-white/[0.08] p-4 space-y-3">
          {agents.length === 0 ? <p className="text-[#94A3B8]">Aucun agent configure.</p> : null}
          {agents.map((agent) => (
            <div key={agent.id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 rounded-lg bg-white/[0.03]">
              <div>
                <p className="text-white font-medium">{agent.name}</p>
                <p className="text-xs text-[#94A3B8]">{agent.function_type} • {agent.enabled ? "active" : "desactive"}</p>
              </div>
              <Button onClick={() => onRunAgent(agent.id)} disabled={!agent.enabled}>
                Lancer cet agent
              </Button>
            </div>
          ))}
        </div>
      ) : null}

      {view === "create" ? (
        <form onSubmit={onCreateAgent} className="rounded-xl bg-[#0F0F0F] border border-white/[0.08] p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-[#94A3B8]">Nom agent</Label>
              <Input value={createForm.name} onChange={(e) => setCreateForm((p) => ({ ...p, name: e.target.value }))} required />
            </div>
            <div className="space-y-2">
              <Label className="text-[#94A3B8]">Fonction</Label>
              <Input value={createForm.function_type} onChange={(e) => setCreateForm((p) => ({ ...p, function_type: e.target.value }))} required />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label className="text-[#94A3B8]">Max profils</Label>
              <Input type="number" value={createForm.max_profiles} onChange={(e) => setCreateForm((p) => ({ ...p, max_profiles: Number(e.target.value || 0) }))} />
            </div>
            <div className="space-y-2">
              <Label className="text-[#94A3B8]">Max rezilta pa platfòm (dekouvèt)</Label>
              <Input type="number" value={createForm.youtube_max_results} onChange={(e) => setCreateForm((p) => ({ ...p, youtube_max_results: Number(e.target.value || 0) }))} />
            </div>
            <div className="space-y-2">
              <Label className="text-[#94A3B8]">Etat</Label>
              <select
                className="w-full bg-[#050505] border border-white/[0.08] rounded-md px-3 py-2 text-white"
                value={createForm.enabled ? "active" : "off"}
                onChange={(e) => setCreateForm((p) => ({ ...p, enabled: e.target.value === "active" }))}
              >
                <option value="active">Actif</option>
                <option value="off">Desactive</option>
              </select>
            </div>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-[#94A3B8]">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={createForm.discover_youtube} onChange={(e) => setCreateForm((p) => ({ ...p, discover_youtube: e.target.checked }))} />
              YouTube
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={createForm.discover_tiktok} onChange={(e) => setCreateForm((p) => ({ ...p, discover_tiktok: e.target.checked }))} />
              TikTok
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={createForm.discover_instagram} onChange={(e) => setCreateForm((p) => ({ ...p, discover_instagram: e.target.checked }))} />
              Instagram
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={createForm.discover_facebook} onChange={(e) => setCreateForm((p) => ({ ...p, discover_facebook: e.target.checked }))} />
              Facebook
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={createForm.dry_run} onChange={(e) => setCreateForm((p) => ({ ...p, dry_run: e.target.checked }))} />
              Dry run
            </label>
          </div>
          <Button type="submit" disabled={createBusy}>
            {createBusy ? "Kreyasyon an kous..." : "Creer agent"}
          </Button>
          {createBusy ? (
            <p className="text-xs text-[#94A3B8]">Anrejistreman imedyat — senkronizasyon Supabase an aryè.</p>
          ) : null}
          {createFlash ? (
            <p className="text-sm text-emerald-400/90" role="status">
              {createFlash}
            </p>
          ) : null}
        </form>
      ) : null}

      {view === "config" ? (
        <form onSubmit={onSaveConfig} className="rounded-xl bg-[#0F0F0F] border border-white/[0.08] p-4 space-y-4">
          <div className="space-y-2">
            <Label className="text-[#94A3B8]">Selectionner agent</Label>
            <select
              className="w-full bg-[#050505] border border-white/[0.08] rounded-md px-3 py-2 text-white"
              value={selectedAgentId}
              onChange={(e) => setSelectedAgentId(e.target.value)}
            >
              {agents.map((a) => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
          </div>
          {selectedAgent ? (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-[#94A3B8]">Nom</Label>
                  <Input value={configForm.name} onChange={(e) => setConfigForm((p) => ({ ...p, name: e.target.value }))} />
                </div>
                <div className="space-y-2">
                  <Label className="text-[#94A3B8]">Fonction</Label>
                  <Input value={configForm.function_type} onChange={(e) => setConfigForm((p) => ({ ...p, function_type: e.target.value }))} />
                </div>
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-[#94A3B8]">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={configForm.enabled} onChange={(e) => setConfigForm((p) => ({ ...p, enabled: e.target.checked }))} />
                  Agent actif
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={configForm.discover_youtube} onChange={(e) => setConfigForm((p) => ({ ...p, discover_youtube: e.target.checked }))} />
                  YouTube
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={configForm.discover_tiktok} onChange={(e) => setConfigForm((p) => ({ ...p, discover_tiktok: e.target.checked }))} />
                  TikTok
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={configForm.discover_instagram} onChange={(e) => setConfigForm((p) => ({ ...p, discover_instagram: e.target.checked }))} />
                  Instagram
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={configForm.discover_facebook} onChange={(e) => setConfigForm((p) => ({ ...p, discover_facebook: e.target.checked }))} />
                  Facebook
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={configForm.dry_run} onChange={(e) => setConfigForm((p) => ({ ...p, dry_run: e.target.checked }))} />
                  Dry run
                </label>
              </div>
              <div className="flex flex-wrap gap-2 items-center">
                <Button type="submit">Sauvegarder configuration</Button>
                <Button type="button" variant="destructive" onClick={onDeleteAgent}>
                  Siprime agent
                </Button>
              </div>
            </>
          ) : (
            <p className="text-[#94A3B8]">Aucun agent disponible.</p>
          )}
        </form>
      ) : null}

      {view === "results" ? (
        <div className="rounded-xl bg-[#0F0F0F] border border-white/[0.08] p-4 space-y-2">
          {runs.length === 0 ? <p className="text-[#94A3B8]">Aucun resultat d'agent.</p> : null}
          {runs.map((run) => (
            <div key={run.id} className="p-3 rounded-lg bg-white/[0.03]">
              <p className="text-white font-medium">{run.agent_name || "Agent rapide"} • {run.status}</p>
              <p className="text-xs text-[#94A3B8]">{run.started_at}</p>
              <p className="text-sm text-[#CBD5E1] mt-1">{run.summary}</p>
            </div>
          ))}
        </div>
      ) : null}

      {view === "search" ? (
        <div className="space-y-6 rounded-xl bg-[#0F0F0F] border border-white/[0.08] p-4">
          <div>
            <h2 className="text-lg font-semibold text-white">Rechèch fòmatè (API .env)</h2>
            <p className="text-sm text-[#94A3B8] mt-1">
              Sa a itilize kle backend ou yo: YouTube, Apify (TikTok / Instagram / Facebook), OpenAI (analiz), Resend (imèl).
              Pa bezwen mete kle yo nan React — yo deja nan backend/.env.
            </p>
            <p className="text-xs text-[#64748B] mt-2 rounded-md bg-white/[0.04] px-3 py-2 border border-white/[0.06]">
              <strong className="text-[#94A3B8]">Tan repons:</strong> Apify dwe fini yon &quot;actor&quot; sou sèvè yo — souvan{" "}
              <strong className="text-[#CBD5E1]">30–90 segonn</strong>, pa egzanp si TikTok chaje. YouTube ak Apify kounye a
              kouri <strong className="text-[#CBD5E1]">an paralèl</strong>. Redwi kantite a (egz. 8) epi dechoche platfòm ki pa
              nesesè pou pi vit.
            </p>
            <p className="text-xs text-[#64748B] mt-2 rounded-md bg-white/[0.04] px-3 py-2 border border-white/[0.06]">
              <strong className="text-[#94A3B8]">Localhost:</strong> navigatè a pale ak backend ou a; se{" "}
              <strong className="text-[#CBD5E1]">sèvè a</strong> ki rele Apify / YouTube. Localhost pa anpeche jwenn pwofil. Si
              ou wè <strong className="text-[#CBD5E1]">0</strong>, souvan se: quota API, hashtags twò etwat, oswa twòp platfòm
              ansanm (nou deduplike pa non itilizatè) — eseye hashtags ou menm, ogmante kantite a, oswa mwens platfòm.
            </p>
          </div>

          {agentApiStatus ? (
            <div className="flex flex-wrap gap-2 text-xs text-[#94A3B8]">
              <span className={agentApiStatus.youtube_configured ? "text-emerald-400" : ""}>
                YouTube: {agentApiStatus.youtube_configured ? "OK" : "manke"}
              </span>
              <span className={agentApiStatus.apify_configured ? "text-emerald-400" : ""}>
                Apify: {agentApiStatus.apify_configured ? "OK" : "manke"}
              </span>
              <span className={agentApiStatus.openai_configured ? "text-emerald-400" : ""}>
                OpenAI: {agentApiStatus.openai_configured ? "OK" : "manke"}
              </span>
              <span className={agentApiStatus.resend_configured ? "text-emerald-400" : ""}>
                Resend: {agentApiStatus.resend_configured ? "OK" : "manke"}
              </span>
            </div>
          ) : null}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-[#94A3B8]">Kategori</Label>
              <select
                className="w-full bg-[#050505] border border-white/[0.08] rounded-md px-3 py-2 text-white text-sm"
                value={searchCategory}
                onChange={(e) => setSearchCategory(e.target.value)}
              >
                {categoriesForSearch.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label className="text-[#94A3B8]">Kantite maksimòm</Label>
              <Input
                type="number"
                min={1}
                max={100}
                value={maxSearchResults}
                onChange={(e) => setMaxSearchResults(Number(e.target.value || 15))}
                className="bg-[#050505] border-white/[0.08]"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-[#94A3B8]">Platfòm</Label>
            <div className="flex flex-wrap gap-4 text-sm text-[#CBD5E1]">
              {PLATFORM_OPTIONS.map((o) => (
                <label key={o.id} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={platformsPick[o.id]}
                    onChange={() => togglePlatform(o.id)}
                  />
                  {o.label}
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label className="text-[#94A3B8]">Hashtags (opsyonèl, Apify + YouTube)</Label>
            <p className="text-xs text-[#64748B]">
              Antre youn oswa plizyè (vègile, espas oswa virgul). Yo aplike sou TikTok, Instagram, Facebook; YouTube ajoute
              requètes dapre menm mo yo. Si ou kite vid, backend itilize hashtags kategori a.
            </p>
            <div className="flex flex-wrap gap-2">
              <Input
                type="text"
                placeholder="egzanp: edikasyon, ayiti, kreyol"
                value={hashtagInput}
                onChange={(e) => setHashtagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addHashtagsFromInput();
                  }
                }}
                className="flex-1 min-w-[200px] bg-[#050505] border-white/[0.08]"
              />
              <Button
                type="button"
                variant="outline"
                onClick={addHashtagsFromInput}
                className="border-white/[0.12] text-white hover:bg-white/[0.06]"
              >
                Ajoute
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={applyCategoryHashtagSuggestions}
                className="border-white/[0.12] text-white hover:bg-white/[0.06]"
              >
                Sijesyon kategori
              </Button>
              {searchHashtags.length ? (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setSearchHashtags([])}
                  className="border-white/[0.12] text-[#94A3B8] hover:bg-white/[0.06]"
                >
                  Efase tout
                </Button>
              ) : null}
            </div>
            {searchHashtags.length ? (
              <div className="flex flex-wrap gap-2">
                {searchHashtags.map((tag, idx) => (
                  <span
                    key={`${tag}-${idx}`}
                    className="inline-flex items-center gap-1 rounded-full bg-white/[0.08] px-2 py-0.5 text-xs text-[#E2E8F0]"
                  >
                    #{tag}
                    <button
                      type="button"
                      className="text-[#94A3B8] hover:text-white ml-0.5"
                      aria-label={`Retire ${tag}`}
                      onClick={() => setSearchHashtags((prev) => prev.filter((_, i) => i !== idx))}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[#64748B]">Oken hashtag personèl — default kategori ap itilize.</p>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              onClick={onRunMultiSearch}
              disabled={searchBusy}
              className="bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              {searchBusy ? "Ap chèche..." : "Lanse rechèch"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onRunCreoleAnalyze}
              disabled={analyzeBusy || !discoveredProfiles.length}
              className="border-white/[0.12] text-white hover:bg-white/[0.06]"
            >
              {analyzeBusy ? "Ap analize..." : "Analize kreyòl (>70)"}
            </Button>
          </div>

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#94A3B8]">
              Pwofil jwenn ({discoveredProfiles.length})
            </p>
            <div className="max-h-[360px] overflow-y-auto space-y-2 rounded-lg border border-white/[0.06] p-2">
              {discoveredProfiles.length === 0 ? (
                <p className="text-sm text-[#64748B] p-2">Poko gen rezilta.</p>
              ) : (
                discoveredProfiles.map((p) => (
                  <div
                    key={p.id || `${p.platform}-${p.username}`}
                    className="rounded-md bg-white/[0.04] px-3 py-2 text-sm"
                  >
                    <p className="text-white font-medium">
                      {p.username}{" "}
                      <span className="text-[#94A3B8] font-normal">· {p.platform}</span>
                      {p.creole_score > 0 ? (
                        <span className="text-emerald-400 ml-2">score kreyòl: {p.creole_score}</span>
                      ) : null}
                    </p>
                    <p className="text-xs text-[#64748B] truncate">{p.profile_url || p.bio?.slice(0, 120)}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          <p className="text-xs text-[#64748B]">
            Apre analiz, gade tab Dashboard pou leads. Pou voye imèl, sèvi ak tablo Leads (lè Resend + imèl sou pwofil la).
          </p>
        </div>
      ) : null}
    </div>
  );
};

