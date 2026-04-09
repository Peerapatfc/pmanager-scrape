import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import { LayoutDashboard, Users, ArrowRightLeft, Bot, Swords, Shield, CalendarDays, LogOut } from 'lucide-react';
import { logout } from './login/actions';
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
            <Link href="/opponent-scout" className="flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors text-orange-400 hover:text-orange-300 hover:bg-orange-900/20">
              <Swords size={20} />
              <span>Opponent Scout</span>
            </Link>
            <Link href="/squad" className="flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors text-indigo-400 hover:text-indigo-300 hover:bg-indigo-900/20">
              <Shield size={20} />
              <span>My Squad</span>
            </Link>
            <Link href="/fixtures" className="flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors text-rose-400 hover:text-rose-300 hover:bg-rose-900/20">
              <CalendarDays size={20} />
              <span>Match Prep</span>
            </Link>
          </nav>
          <div className="p-4 border-t border-neutral-800">
            <form action={logout}>
              <button
                type="submit"
                className="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-neutral-800 transition-colors text-neutral-500 hover:text-neutral-300 w-full"
              >
                <LogOut size={20} />
                <span>Sign Out</span>
              </button>
            </form>
          </div>
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
              <Link href="/opponent-scout" className="text-orange-400 hover:text-orange-300"><Swords size={20} /></Link>
              <Link href="/squad" className="text-indigo-400 hover:text-indigo-300"><Shield size={20} /></Link>
              <Link href="/fixtures" className="text-rose-400 hover:text-rose-300"><CalendarDays size={20} /></Link>
              <form action={logout}>
                <button type="submit" className="text-neutral-500 hover:text-neutral-300">
                  <LogOut size={20} />
                </button>
              </form>
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
