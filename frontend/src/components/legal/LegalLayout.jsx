import { NavLink, Outlet } from "react-router-dom";

const tabClass = ({ isActive }) =>
  `rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
    isActive
      ? "bg-emerald-100 text-emerald-950"
      : "bg-transparent text-gray-500 hover:text-gray-300"
  }`;

export const LegalLayout = () => {
  return (
    <div className="min-h-screen bg-black text-gray-400 flex flex-col">
      <div className="mx-auto w-full max-w-3xl flex-1 px-6 py-8 pb-32 sm:px-8">
        <div className="mb-6 flex flex-wrap gap-2">
          <NavLink to="/legal/privacy" className={tabClass} end>
            Politik Konfidansyalite
          </NavLink>
          <NavLink to="/legal/terms" className={tabClass} end>
            Kondisyon Itilizasyon
          </NavLink>
          <NavLink to="/legal/cookies" className={tabClass} end>
            Politik sou Kòki
          </NavLink>
        </div>
        <Outlet />
      </div>

      <footer className="pointer-events-none fixed bottom-6 left-0 right-0 z-10 flex justify-center px-4">
        <div className="pointer-events-auto flex max-w-full flex-wrap items-center justify-center gap-x-2 gap-y-1 rounded-full border border-black/5 bg-[#F5F0E8] px-5 py-3 text-center text-xs text-neutral-800 shadow-lg sm:text-sm">
          <span>© 2026 KonekteGroup. Tout dwa rezève.</span>
          <span className="hidden sm:inline">—</span>
          <a
            href="https://agentai.konektegroup.com"
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-blue-600 hover:text-blue-700 hover:underline"
          >
            agentai.konektegroup.com
          </a>
        </div>
      </footer>
    </div>
  );
};
