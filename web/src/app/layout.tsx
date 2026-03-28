import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import { LayoutDashboard, Users, ArrowRightLeft, Bot } from 'lucide-react';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'PManager Dashboard',
  description: 'Supabase Data Visualization for PManager Scraper',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-neutral-900 text-neutral-100 min-h-screen flex`}>
        {/* Sidebar */}
        <aside className="w-64 bg-neutral-950 border-r border-neutral-800 hidden md:flex flex-col">
          <div className="p-6 border-b border-neutral-800">
            <h1 className="text-xl font-bold bg-linear-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              PM Dashboard
            </h1>
          </div>
          <nav className="flex-1 p-4 space-y-2">
            <Link href="/" className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-neutral-800 transition-colors text-neutral-300 hover:text-white">
              <LayoutDashboard size={20} />
              <span>Dashboard</span>
            </Link>
            <Link href="/players" className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-neutral-800 transition-colors text-neutral-300 hover:text-white">
              <Users size={20} />
              <span>All Players</span>
            </Link>
            <Link href="/transfers" className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-neutral-800 transition-colors text-neutral-300 hover:text-white">
              <ArrowRightLeft size={20} />
              <span>Transfers</span>
            </Link>
            <Link href="/bot-opportunities" className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-neutral-800 transition-colors text-purple-400 hover:text-purple-300 hover:bg-purple-900/20">
              <Bot size={20} />
              <span>Bot Opportunities</span>
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-h-screen">
          {/* Mobile Header */}
          <header className="md:hidden flex items-center justify-between p-4 bg-neutral-950 border-b border-neutral-800">
            <h1 className="text-lg font-bold bg-linear-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
              PM Dashboard
            </h1>
            <nav className="flex space-x-4">
              <Link href="/" className="text-neutral-400 hover:text-white"><LayoutDashboard size={20} /></Link>
              <Link href="/players" className="text-neutral-400 hover:text-white"><Users size={20} /></Link>
              <Link href="/transfers" className="text-neutral-400 hover:text-white"><ArrowRightLeft size={20} /></Link>
              <Link href="/bot-opportunities" className="text-purple-400 hover:text-purple-300"><Bot size={20} /></Link>
            </nav>
          </header>

          <main className="flex-1 p-4 md:p-8 overflow-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
