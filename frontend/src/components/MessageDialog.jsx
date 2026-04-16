import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "../components/ui/dialog";
import { Button } from "../components/ui/button";
import { Copy, Check, RefreshCw } from "lucide-react";
import { useState } from "react";

export const MessageDialog = ({ open, onOpenChange, lead, onRegenerate }) => {
  const [copied, setCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const handleCopy = async () => {
    if (!lead?.generated_message) return;
    await navigator.clipboard.writeText(lead.generated_message);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRegenerate = async () => {
    if (!lead?.id || !onRegenerate) return;
    setRegenerating(true);
    await onRegenerate(lead.id);
    setRegenerating(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-[#0F0F0F] border-white/[0.08] text-white max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-heading text-lg text-white">
            Message pour {lead?.name}
          </DialogTitle>
          <DialogDescription className="text-[#94A3B8] text-sm">
            Message de recrutement genere par l'IA
          </DialogDescription>
        </DialogHeader>

        <div className="mt-4 space-y-4">
          <div
            data-testid="generated-message-text"
            className="p-4 rounded-lg bg-[#050505] border border-white/[0.08] text-[#F8FAFC] text-sm leading-relaxed font-body whitespace-pre-wrap"
          >
            {lead?.generated_message || "Aucun message genere."}
          </div>

          <div className="flex gap-2">
            <Button
              data-testid="copy-message-btn"
              onClick={handleCopy}
              variant="outline"
              className="flex-1 bg-transparent border-white/[0.08] text-[#F8FAFC] hover:bg-white/[0.05] hover:text-white"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 mr-2" /> Copie !
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 mr-2" /> Copier
                </>
              )}
            </Button>
            <Button
              data-testid="regenerate-message-btn"
              onClick={handleRegenerate}
              disabled={regenerating}
              className="flex-1 bg-[#2563EB] hover:bg-[#1D4ED8] text-white"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${regenerating ? "animate-spin" : ""}`} />
              {regenerating ? "Generation..." : "Regenerer"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
