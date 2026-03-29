import { supabase } from "@/lib/supabase";
import { Users, ArrowRightLeft, TrendingUp, Bot } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

export const revalidate = 60;

interface Stats {
  players: number;
  transfers: number;
  bots: number;
}

interface StatsCardProps {
  title: string;
  count: number;
  icon: ReactNode;
  iconBg: string;
  hoverBorder: string;
  linkHref: string;
  linkLabel: string;
  linkColor: string;
}

function StatsCard({
  title,
  count,
  icon,
  iconBg,
  hoverBorder,
  linkHref,
  linkLabel,
  linkColor,
}: StatsCardProps) {
  return (
    <div
      className={`bg-neutral-900 border border-neutral-800 rounded-xl p-6 shadow-lg shadow-black/50 ${hoverBorder} transition-colors`}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-neutral-200">{title}</h3>
        <div className={`p-3 ${iconBg} rounded-lg`}>{icon}</div>
      </div>
      <p className="text-4xl font-bold text-white mb-2">{count}</p>
      <Link href={linkHref} className={`text-sm ${linkColor} flex items-center hover:underline`}>
        {linkLabel} <TrendingUp size={16} className="ml-1" />
      </Link>
    </div>
  );
}

async function getStats(): Promise<Stats> {
  const [{ count: playersCount }, { count: transfersCount }, { count: botCount }] =
    await Promise.all([
      supabase.from("players").select("*", { count: "exact", head: true }),
      supabase.from("transfer_listings").select("*", { count: "exact", head: true }),
      supabase.from("bot_opportunities").select("*", { count: "exact", head: true }),
    ]);

  return {
    players: playersCount ?? 0,
    transfers: transfersCount ?? 0,
    bots: botCount ?? 0,
  };
}

export default async function DashboardPage() {
  const stats = await getStats();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold bg-linear-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent mb-2">
          Dashboard Overview
        </h1>
        <p className="text-neutral-400">
          Welcome to the PManager Scraper Dashboard. View the latest stats from your Supabase database.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatsCard
          title="Total Players"
          count={stats.players}
          icon={<Users size={24} />}
          iconBg="bg-emerald-500/10 text-emerald-400"
          hoverBorder="hover:border-emerald-500/50"
          linkHref="/players"
          linkLabel="View all players"
          linkColor="text-emerald-400"
        />
        <StatsCard
          title="Transfer Listings"
          count={stats.transfers}
          icon={<ArrowRightLeft size={24} />}
          iconBg="bg-cyan-500/10 text-cyan-400"
          hoverBorder="hover:border-cyan-500/50"
          linkHref="/transfers"
          linkLabel="View all transfers"
          linkColor="text-cyan-400"
        />
        <StatsCard
          title="Bot Opportunities"
          count={stats.bots}
          icon={<Bot size={24} />}
          iconBg="bg-purple-500/10 text-purple-400"
          hoverBorder="hover:border-purple-500/50"
          linkHref="/bot-opportunities"
          linkLabel="View bot targets"
          linkColor="text-purple-400"
        />
      </div>
    </div>
  );
}
