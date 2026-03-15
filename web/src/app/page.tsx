import { supabase } from '@/lib/supabase';
import { Users, ArrowRightLeft, TrendingUp } from 'lucide-react';
import Link from 'next/link';

export const revalidate = 60; // Revalidate every 60 seconds

async function getStats() {
  const { count: playersCount } = await supabase
    .from('players')
    .select('*', { count: 'exact', head: true });

  const { count: transfersCount } = await supabase
    .from('transfer_listings')
    .select('*', { count: 'exact', head: true });

  return {
    players: playersCount || 0,
    transfers: transfersCount || 0,
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
        {/* Players Card */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 shadow-lg shadow-black/50 hover:border-emerald-500/50 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-neutral-200">Total Players</h3>
            <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <Users size={24} />
            </div>
          </div>
          <p className="text-4xl font-bold text-white mb-2">{stats.players}</p>
          <Link href="/players" className="text-sm text-emerald-400 flex items-center hover:underline">
            View all players <TrendingUp size={16} className="ml-1" />
          </Link>
        </div>

        {/* Transfers Card */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 shadow-lg shadow-black/50 hover:border-cyan-500/50 transition-colors">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-neutral-200">Transfer Listings</h3>
            <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-lg">
              <ArrowRightLeft size={24} />
            </div>
          </div>
          <p className="text-4xl font-bold text-white mb-2">{stats.transfers}</p>
          <Link href="/transfers" className="text-sm text-cyan-400 flex items-center hover:underline">
            View all transfers <TrendingUp size={16} className="ml-1" />
          </Link>
        </div>
      </div>
    </div>
  );
}
