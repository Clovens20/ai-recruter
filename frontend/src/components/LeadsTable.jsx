import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Button } from "../components/ui/button";
import { ScoreBadge } from "./ScoreBadge";
import { StatusBadge } from "./StatusBadge";
import { PlatformBadge } from "./PlatformBadge";
import { MessageDialog } from "./MessageDialog";
import {
  MessageSquare,
  MoreVertical,
  Trash2,
  ArrowUpDown,
  Filter,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export const LeadsTable = ({ leads, onStatusChange, onDelete, onRegenerate, loading }) => {
  const [selectedLead, setSelectedLead] = useState(null);
  const [messageOpen, setMessageOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");
  const [platformFilter, setPlatformFilter] = useState("all");
  const [scoreSort, setScoreSort] = useState("desc");

  const filtered = leads
    .filter((l) => statusFilter === "all" || l.status === statusFilter)
    .filter((l) => platformFilter === "all" || l.platform === platformFilter)
    .sort((a, b) => (scoreSort === "desc" ? b.score - a.score : a.score - b.score));

  const openMessage = (lead) => {
    setSelectedLead(lead);
    setMessageOpen(true);
  };

  return (
    <div data-testid="leads-table-container">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-[#94A3B8]" />
          <span className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
            Filtres
          </span>
        </div>

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger
            data-testid="filter-status"
            className="w-[140px] h-9 bg-[#0F0F0F] border-white/[0.08] text-[#F8FAFC] text-sm"
          >
            <SelectValue placeholder="Statut" />
          </SelectTrigger>
          <SelectContent className="bg-[#0F0F0F] border-white/[0.08]">
            <SelectItem value="all" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">Tous</SelectItem>
            <SelectItem value="new" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">Nouveau</SelectItem>
            <SelectItem value="contacted" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">Contact&eacute;</SelectItem>
            <SelectItem value="replied" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">R&eacute;pondu</SelectItem>
          </SelectContent>
        </Select>

        <Select value={platformFilter} onValueChange={setPlatformFilter}>
          <SelectTrigger
            data-testid="filter-platform"
            className="w-[140px] h-9 bg-[#0F0F0F] border-white/[0.08] text-[#F8FAFC] text-sm"
          >
            <SelectValue placeholder="Plateforme" />
          </SelectTrigger>
          <SelectContent className="bg-[#0F0F0F] border-white/[0.08]">
            <SelectItem value="all" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">Toutes</SelectItem>
            <SelectItem value="youtube" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">YouTube</SelectItem>
            <SelectItem value="tiktok" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">TikTok</SelectItem>
            <SelectItem value="facebook" className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white">Facebook</SelectItem>
          </SelectContent>
        </Select>

        <Button
          data-testid="sort-score-btn"
          variant="outline"
          size="sm"
          onClick={() => setScoreSort(scoreSort === "desc" ? "asc" : "desc")}
          className="h-9 bg-transparent border-white/[0.08] text-[#94A3B8] hover:text-white hover:bg-white/[0.05]"
        >
          <ArrowUpDown className="w-3.5 h-3.5 mr-1.5" />
          Score {scoreSort === "desc" ? "\u2193" : "\u2191"}
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-white/[0.08] overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-white/[0.08] hover:bg-transparent">
              <TableHead className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#94A3B8] h-11">
                Lead
              </TableHead>
              <TableHead className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#94A3B8] h-11">
                Plateforme
              </TableHead>
              <TableHead className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#94A3B8] h-11">
                Domaine
              </TableHead>
              <TableHead className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#94A3B8] h-11">
                Score IA
              </TableHead>
              <TableHead className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#94A3B8] h-11">
                Statut
              </TableHead>
              <TableHead className="text-[11px] font-semibold tracking-[0.08em] uppercase text-[#94A3B8] h-11 text-right">
                Actions
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-12 text-[#94A3B8]">
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-[#2563EB] border-t-transparent rounded-full animate-spin" />
                    Chargement...
                  </div>
                </TableCell>
              </TableRow>
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-12 text-[#94A3B8]">
                  Aucun lead trouve. Analysez un profil pour commencer.
                </TableCell>
              </TableRow>
            ) : (
              <AnimatePresence>
                {filtered.map((lead, i) => (
                  <motion.tr
                    key={lead.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04, duration: 0.25 }}
                    data-testid={`lead-row-${lead.id}`}
                    className="border-white/[0.06] hover:bg-white/[0.03] transition-colors duration-150"
                  >
                    <TableCell className="py-3">
                      <div>
                        <p className="text-sm font-medium text-[#F8FAFC]">{lead.name}</p>
                        <p className="text-xs text-[#64748B] truncate max-w-[200px]">{lead.bio}</p>
                      </div>
                    </TableCell>
                    <TableCell><PlatformBadge platform={lead.platform} /></TableCell>
                    <TableCell className="text-sm text-[#94A3B8] capitalize">{lead.domain}</TableCell>
                    <TableCell><ScoreBadge score={lead.score} /></TableCell>
                    <TableCell><StatusBadge status={lead.status} /></TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          data-testid={`view-message-btn-${lead.id}`}
                          variant="ghost"
                          size="sm"
                          onClick={() => openMessage(lead)}
                          className="h-8 w-8 p-0 text-[#94A3B8] hover:text-[#2563EB] hover:bg-blue-500/10"
                        >
                          <MessageSquare className="w-4 h-4" />
                        </Button>

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              data-testid={`lead-actions-btn-${lead.id}`}
                              variant="ghost"
                              size="sm"
                              className="h-8 w-8 p-0 text-[#94A3B8] hover:text-white hover:bg-white/[0.08]"
                            >
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent className="bg-[#0F0F0F] border-white/[0.08]">
                            <DropdownMenuItem
                              data-testid={`set-status-contacted-${lead.id}`}
                              onClick={() => onStatusChange(lead.id, "contacted")}
                              className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white cursor-pointer"
                            >
                              Marquer Contact&eacute;
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              data-testid={`set-status-replied-${lead.id}`}
                              onClick={() => onStatusChange(lead.id, "replied")}
                              className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white cursor-pointer"
                            >
                              Marquer R&eacute;pondu
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              data-testid={`set-status-new-${lead.id}`}
                              onClick={() => onStatusChange(lead.id, "new")}
                              className="text-[#F8FAFC] focus:bg-white/[0.08] focus:text-white cursor-pointer"
                            >
                              Remettre Nouveau
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              data-testid={`delete-lead-${lead.id}`}
                              onClick={() => onDelete(lead.id)}
                              className="text-red-400 focus:bg-red-500/10 focus:text-red-400 cursor-pointer"
                            >
                              <Trash2 className="w-3.5 h-3.5 mr-2" />
                              Supprimer
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </TableCell>
                  </motion.tr>
                ))}
              </AnimatePresence>
            )}
          </TableBody>
        </Table>
      </div>

      <MessageDialog
        open={messageOpen}
        onOpenChange={setMessageOpen}
        lead={selectedLead}
        onRegenerate={async (id) => {
          await onRegenerate(id);
          // refresh selected lead message
          const updated = leads.find((l) => l.id === id);
          if (updated) setSelectedLead({ ...updated });
        }}
      />
    </div>
  );
};
