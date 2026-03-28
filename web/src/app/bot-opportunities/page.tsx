import { supabase } from '@/lib/supabase';
import { Bot, ExternalLink, Hash, ArrowUpRight, Percent } from 'lucide-react';
import Link from 'next/link';

export const revalidate = 60;

async function getBotOpportunities() {
  const { data, error } = await supabase
    .from('bot_opportunities')
    .select('*')
    .order('profit_margin', { ascending: false });

  if (error) {
    console.error('Error fetching bot opportunities:', error);
    return [];
  }
  return data || [];
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value);
}

export default async function BotOpportunitiesPage() {
  const opportunities = await getBotOpportunities();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent mb-2 flex items-center">
            <Bot className="mr-3 text-purple-400" size={32} />
            Bot Opportunities
          </h1>
          <p className="text-neutral-400">
            Players from BOT teams with asking prices below their estimated values.
          </p>
        </div>
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg px-4 py-2 flex items-center space-x-2">
          <Hash size={18} className="text-purple-400" />
          <span className="font-semibold">{opportunities.length} Targets</span>
        </div>
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden shadow-xl shadow-black/50">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[1000px]">
            <thead>
              <tr className="bg-neutral-950/50 border-b border-neutral-800 text-neutral-400 text-sm">
                <th className="p-4 font-semibold">Player</th>
                <th className="p-4 font-semibold">Age/Pos</th>
                <th className="p-4 font-semibold">Quality</th>
                <th className="p-4 font-semibold">BOT Team</th>
                <th className="p-4 font-semibold text-right">Asking Price</th>
                <th className="p-4 font-semibold text-right">Est. Value</th>
                <th className="p-4 font-semibold text-right">Value Diff</th>
                <th className="p-4 font-semibold text-right">Profit Margin</th>
                <th className="p-4 font-semibold text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/50">
              {opportunities.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-8 text-center text-neutral-500">
                    No bot opportunities found. Run the scraper to populate data.
                  </td>
                </tr>
              ) : (
                opportunities.map((opp) => (
                  <tr key={opp.id} className="hover:bg-neutral-800/30 transition-colors group">
                    <td className="p-4">
                      <div className="font-semibold text-white">{opp.name}</div>
                      <div className="text-xs text-neutral-500">ID: {opp.id}</div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center space-x-2">
                        <span className="text-neutral-300">{opp.age}y</span>
                        <span className="px-2 py-0.5 rounded text-xs bg-neutral-800 text-neutral-300 border border-neutral-700">
                          {opp.position}
                        </span>
                      </div>
                    </td>
                    <td className="p-4">
                      <span className="text-emerald-400 font-medium">{opp.quality}</span>
                    </td>
                    <td className="p-4">
                      <span className="text-neutral-300 flex items-center">
                        <Bot size={14} className="mr-1.5 text-neutral-500" />
                        {opp.team_name}
                      </span>
                    </td>
                    <td className="p-4 text-right font-medium text-white">
                      {formatCurrency(opp.asking_price)}
                    </td>
                    <td className="p-4 text-right text-neutral-400">
                      {formatCurrency(opp.estimated_value)}
                    </td>
                    <td className="p-4 text-right">
                      <span className="text-emerald-400 font-medium flex items-center justify-end">
                        <ArrowUpRight size={14} className="mr-1" />
                        {formatCurrency(opp.value_diff)}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <span className="inline-flex items-center px-2 py-1 rounded bg-purple-500/10 text-purple-400 text-sm font-bold border border-purple-500/20">
                        {opp.profit_margin}%
                        <Percent size={12} className="ml-0.5" />
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <a
                        href={opp.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center justify-center p-2 rounded-lg bg-neutral-800 text-neutral-300 hover:bg-emerald-500/20 hover:text-emerald-400 hover:border-emerald-500/50 border border-transparent transition-all"
                        title="View on PManager"
                      >
                        <ExternalLink size={18} />
                      </a>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
