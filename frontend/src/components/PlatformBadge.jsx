import { FaYoutube, FaTiktok, FaFacebookF } from "react-icons/fa";

const platformConfig = {
  youtube: {
    icon: FaYoutube,
    label: "YouTube",
    color: "text-[#FF0000]",
    bg: "bg-red-500/10",
  },
  tiktok: {
    icon: FaTiktok,
    label: "TikTok",
    color: "text-[#00F2FE]",
    bg: "bg-cyan-500/10",
  },
  facebook: {
    icon: FaFacebookF,
    label: "Facebook",
    color: "text-[#1877F2]",
    bg: "bg-blue-500/10",
  },
};

export const PlatformBadge = ({ platform }) => {
  const config = platformConfig[platform?.toLowerCase()] || platformConfig.facebook;
  const Icon = config.icon;

  return (
    <div
      data-testid={`platform-badge-${platform}`}
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 ${config.bg}`}
    >
      <Icon className={`w-3 h-3 ${config.color}`} />
      <span className="text-[11px] font-medium text-[#F8FAFC]">{config.label}</span>
    </div>
  );
};
