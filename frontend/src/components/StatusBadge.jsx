const statusConfig = {
  new: {
    label: "Nouveau",
    className: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  },
  contacted: {
    label: "Contact\u00e9",
    className: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  },
  replied: {
    label: "R\u00e9pondu",
    className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  },
};

export const StatusBadge = ({ status }) => {
  const config = statusConfig[status] || statusConfig.new;
  return (
    <span
      data-testid={`status-badge-${status}`}
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium border ${config.className}`}
    >
      {config.label}
    </span>
  );
};
