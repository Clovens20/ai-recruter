import { Users, TrendingUp, UserCheck, Clock } from "lucide-react";
import { motion } from "framer-motion";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export const StatsCards = ({ stats }) => {
  const cards = [
    {
      title: "Total Leads",
      value: stats?.total ?? 0,
      icon: Users,
      accent: "text-[#2563EB]",
      bg: "bg-blue-500/10",
    },
    {
      title: "Score Moyen",
      value: stats?.avg_score ? `${stats.avg_score}%` : "0%",
      icon: TrendingUp,
      accent: "text-[#10B981]",
      bg: "bg-emerald-500/10",
    },
    {
      title: "Haut Potentiel",
      value: stats?.high_potential ?? 0,
      icon: UserCheck,
      accent: "text-[#F59E0B]",
      bg: "bg-amber-500/10",
    },
    {
      title: "En Attente",
      value: stats?.by_status?.new ?? 0,
      icon: Clock,
      accent: "text-[#00E5FF]",
      bg: "bg-cyan-500/10",
    },
  ];

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
    >
      {cards.map((card) => (
        <motion.div
          key={card.title}
          variants={item}
          data-testid={`stat-card-${card.title.toLowerCase().replace(/\s/g, "-")}`}
          className="rounded-xl bg-[#0F0F0F] border border-white/[0.08] p-6 transition-colors duration-200 hover:border-white/[0.12]"
        >
          <div className="flex items-center justify-between mb-4">
            <p className="text-[11px] font-semibold tracking-[0.1em] uppercase text-[#94A3B8]">
              {card.title}
            </p>
            <div className={`w-8 h-8 rounded-lg ${card.bg} flex items-center justify-center`}>
              <card.icon className={`w-4 h-4 ${card.accent}`} />
            </div>
          </div>
          <p className="font-heading text-3xl font-bold text-white">{card.value}</p>
        </motion.div>
      ))}
    </motion.div>
  );
};
