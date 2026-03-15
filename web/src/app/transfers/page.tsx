import { supabase } from '@/lib/supabase';
import { ArrowRightLeft } from 'lucide-react';

export const revalidate = 60;

export default async function TransfersPage() {
  const { data: transfers, error } = await supabase
    .from('transfer_listings')
    .select('*')
    .order('roi', { ascending: false })
    .limit(100);

  if (error) {
    console.error('Error fetching transfers:', error);
  }

  // Helper to format currency
  const formatValue = (val: number) => {
    if (!val) return '0';
    return val.toLocaleString('en-US');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent flex items-center gap-3">
            <ArrowRightLeft size={32} className="text-cyan-400" />
            Transfer Listings
          </h1>
          <p className="text-neutral-400 mt-2">
            Top 100 transfer listings ordered by ROI format.
          </p>
        </div>
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden shadow-xl shadow-black/50">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-neutral-400 uppercase bg-neutral-950/50 border-b border-neutral-800">
              <tr>
                <th scope="col" className="px-6 py-4 font-semibold">Player</th>
                <th scope="col" className="px-6 py-4 font-semibold">Pos</th>
                <th scope="col" className="px-6 py-4 font-semibold">Quality</th>
                <th scope="col" className="px-6 py-4 font-semibold">Est. Value</th>
                <th scope="col" className="px-6 py-4 font-semibold">Asking Price</th>
                <th scope="col" className="px-6 py-4 font-semibold">ROI (%)</th>
                <th scope="col" className="px-6 py-4 font-semibold">Deadline</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60">
              {transfers?.map((tx) => (
                <tr key={tx.id} className="hover:bg-neutral-800/50 transition-colors">
                  <td className="px-6 py-4 font-medium text-white flex flex-col gap-1">
                    {tx.url ? (
                      <a href={tx.url} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 hover:underline">
                        {tx.name}
                      </a>
                    ) : (
                      tx.name
                    )}
                    <span className="text-neutral-500 text-xs text-nowrap">Age: {tx.age} | Pot: {tx.potential}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 rounded-md bg-neutral-800 text-neutral-300 text-xs font-medium">
                      {tx.position}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-emerald-400 font-medium">{tx.quality}</td>
                  <td className="px-6 py-4 text-neutral-300 font-medium">
                    ${formatValue(tx.estimated_value)}
                  </td>
                  <td className="px-6 py-4 font-medium text-neutral-100">
                    ${formatValue(tx.asking_price)}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2.5 py-1 rounded-md text-xs font-bold ${
                      (tx.roi || 0) > 200 ? 'bg-emerald-500/20 text-emerald-400' :
                      (tx.roi || 0) > 100 ? 'bg-blue-500/20 text-blue-400' :
                      'bg-neutral-800 text-neutral-300'
                    }`}>
                      {tx.roi}%
                    </span>
                  </td>
                  <td className="px-6 py-4 text-neutral-400 whitespace-nowrap">{tx.deadline}</td>
                </tr>
              ))}
              {(!transfers || transfers.length === 0) && (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-neutral-500">
                    No transfer listings found in the database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
