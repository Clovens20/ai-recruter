import { NavLink } from "react-router-dom";
import { LayoutDashboard, UserSearch, Sparkles } from "lucide-react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/analyze", icon: UserSearch, label: "Analyser" },
];

export const Sidebar = () => {
  return (
    <aside
      data-testid="sidebar"
      className="fixed left-0 top-0 h-screen w-64 bg-[#050505] border-r border-white/[0.08] flex flex-col z-40"
    >
      {/* Logo */}
      <div className="p-6 border-b border-white/[0.08]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#2563EB] flex items-center justify-center ai-glow">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-heading text-lg font-bold text-white tracking-tight leading-none">
              Konekte
            </h1>
            <p className="text-[10px] font-medium tracking-[0.15em] uppercase text-[#94A3B8]">
              AI Recruiter
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        <p className="text-[10px] font-semibold tracking-[0.12em] uppercase text-[#94A3B8] px-3 mb-3">
          Menu
        </p>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            data-testid={`nav-${item.label.toLowerCase()}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200 ${
                isActive
                  ? "bg-white/10 text-white"
                  : "text-[#94A3B8] hover:text-white hover:bg-white/[0.05]"
              }`
            }
          >
            <item.icon className="w-[18px] h-[18px]" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom info */}
      <div className="p-4 border-t border-white/[0.08]">
        <div className="px-3 py-2">
          <p className="text-[11px] text-[#94A3B8]">Konekte Group</p>
          <p className="text-[10px] text-[#64748B]">Agent v1.0</p>
        </div>
      </div>
    </aside>
  );
};
