export const ScoreBadge = ({ score }) => {
  const getColor = () => {
    if (score >= 70) return { stroke: "#10B981", text: "text-[#10B981]", bg: "bg-emerald-500/10" };
    if (score >= 40) return { stroke: "#F59E0B", text: "text-[#F59E0B]", bg: "bg-amber-500/10" };
    return { stroke: "#EF4444", text: "text-[#EF4444]", bg: "bg-red-500/10" };
  };

  const { stroke, text, bg } = getColor();
  const circumference = 2 * Math.PI * 16;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex items-center gap-2" data-testid="score-badge">
      <div className="relative w-10 h-10">
        <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
          <circle
            cx="18" cy="18" r="16"
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="2.5"
          />
          <circle
            cx="18" cy="18" r="16"
            fill="none"
            stroke={stroke}
            strokeWidth="2.5"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ animation: "score-fill 1s ease-out forwards" }}
          />
        </svg>
        <span className={`absolute inset-0 flex items-center justify-center text-[11px] font-bold ${text}`}>
          {score}
        </span>
      </div>
    </div>
  );
};
