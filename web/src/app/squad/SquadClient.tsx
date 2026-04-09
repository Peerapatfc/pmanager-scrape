"use client";

import { useMemo, useState } from "react";
import { Shield } from "lucide-react";
import { skillTier } from "@/lib/skillTier";
import type { SquadPlayer } from "./page";

// ── Skill display order (abbreviation → DB field name) ──────────────────────
const SKILLS: { abbr: string; field: string }[] = [
  { abbr: "Han", field: "Handling" },
  { abbr: "Cro", field: "Out of Area" },
  { abbr: "Ref", field: "Reflexes" },
  { abbr: "Agi", field: "Agility" },
  { abbr: "Tck", field: "Tackling" },
  { abbr: "Hea", field: "Heading" },
  { abbr: "Pas", field: "Passing" },
  { abbr: "Pos", field: "Positioning" },
  { abbr: "Fin", field: "Finishing" },
  { abbr: "Tec", field: "Technique" },
  { abbr: "Spe", field: "Speed" },
  { abbr: "Str", field: "Strength" },
];

// ── Position helpers ─────────────────────────────────────────────────────────
type PosGroup = "GK" | "D" | "M" | "F";

function posGroup(position: string): PosGroup {
  const p = position.trim().toUpperCase();
  if (p.startsWith("GK")) return "GK";
  if (p.startsWith("D")) return "D";
  if (p.startsWith("M")) return "M";
  return "F";
}

const POS_ORDER: PosGroup[] = ["GK", "D", "M", "F"];
const POS_LABEL: Record<PosGroup, string> = {
  GK: "Goalkeepers",
  D: "Defenders",
  M: "Midfielders",
  F: "Forwards",
};
const POS_COLORS: Record<PosGroup, { badge: string; border: string; text: string }> = {
  GK: { badge: "bg-yellow-500/20 text-yellow-400",  border: "border-yellow-500/30", text: "text-yellow-400" },
  D:  { badge: "bg-blue-500/20 text-blue-400",      border: "border-blue-500/30",   text: "text-blue-400"   },
  M:  { badge: "bg-emerald-500/20 text-emerald-400", border: "border-emerald-500/30", text: "text-emerald-400" },
  F:  { badge: "bg-red-500/20 text-red-400",        border: "border-red-500/30",    text: "text-red-400"    },
};

// ── Skill helper ─────────────────────────────────────────────────────────────
function sk(player: SquadPlayer, field: string): number {
  return player.skills?.[field] ?? 0;
}

function avg(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((s, v) => s + v, 0) / values.length;
}

// ── Tactical rating definitions ───────────────────────────────────────────────
interface TacticalMetric {
  label: string;
  compute: (players: SquadPlayer[], all: SquadPlayer[]) => number | null;
}

const TACTICAL_METRICS: TacticalMetric[] = [
  {
    label: "Speed",
    compute: (_, all) => avg(all.map((p) => sk(p, "Speed"))),
  },
  {
    label: "Strength",
    compute: (_, all) => avg(all.map((p) => sk(p, "Strength"))),
  },
  {
    label: "Offside Trap",
    compute: (_, all) => {
      const defs = all.filter((p) => posGroup(p.position) === "D");
      if (!defs.length) return null;
      return avg(defs.map((p) => (sk(p, "Positioning") + sk(p, "Speed")) / 2));
    },
  },
  {
    label: "Pressing – High",
    compute: (_, all) => avg(all.map((p) => (sk(p, "Speed") + sk(p, "Passing")) / 2)),
  },
  {
    label: "Pressing – Low",
    compute: (_, all) =>
      avg(all.map((p) => (sk(p, "Tackling") + (20 - sk(p, "Speed"))) / 2)),
  },
  {
    label: "Counter Attack",
    compute: (_, all) => avg(all.map((p) => (sk(p, "Speed") + sk(p, "Passing")) / 2)),
  },
  {
    label: "High Balls",
    compute: (_, all) => avg(all.map((p) => (sk(p, "Heading") + sk(p, "Strength")) / 2)),
  },
  {
    label: "One on Ones",
    compute: (_, all) => {
      const mf = all.filter((p) => ["M", "F"].includes(posGroup(p.position)));
      if (!mf.length) return null;
      return avg(mf.map((p) => (sk(p, "Technique") + sk(p, "Strength")) / 2));
    },
  },
  {
    label: "Keeping – Stand In",
    compute: (_, all) => {
      const gks = all.filter((p) => posGroup(p.position) === "GK");
      if (!gks.length) return null;
      return avg(gks.map((p) => (sk(p, "Reflexes") + sk(p, "Handling")) / 2));
    },
  },
  {
    label: "Keeping – Rush Out",
    compute: (_, all) => {
      const gks = all.filter((p) => posGroup(p.position) === "GK");
      if (!gks.length) return null;
      return avg(gks.map((p) => (sk(p, "Agility") + sk(p, "Out of Area")) / 2));
    },
  },
  {
    label: "Marking – Zonal",
    compute: (_, all) => {
      const dm = all.filter((p) => ["D", "M"].includes(posGroup(p.position)));
      if (!dm.length) return null;
      return avg(dm.map((p) => (sk(p, "Speed") + sk(p, "Tackling")) / 2));
    },
  },
  {
    label: "Marking – Man to Man",
    compute: (_, all) => {
      const dm = all.filter((p) => ["D", "M"].includes(posGroup(p.position)));
      if (!dm.length) return null;
      return avg(dm.map((p) => (sk(p, "Strength") + sk(p, "Tackling")) / 2));
    },
  },
  {
    label: "Long Shots",
    compute: (_, all) => {
      const mf = all.filter((p) => ["M", "F"].includes(posGroup(p.position)));
      if (!mf.length) return null;
      return avg(mf.map((p) => (sk(p, "Finishing") + sk(p, "Technique")) / 2));
    },
  },
  {
    label: "First Time Shots",
    compute: (_, all) => {
      const fwds = all.filter((p) => posGroup(p.position) === "F");
      if (fwds.length < 3) return null; // requires at least 3 forwards
      return avg(fwds.map((p) => (sk(p, "Finishing") + sk(p, "Heading")) / 2));
    },
  },
];

// ── Sub-components ────────────────────────────────────────────────────────────

function SkillChip({ value }: { value: number }) {
  const tier = skillTier(value);
  return (
    <div
      className="w-full h-6 rounded flex items-center justify-center text-[10px] font-bold text-white"
      style={{ backgroundColor: tier.bg }}
      title={`${value} — ${tier.label}`}
    >
      {value}
    </div>
  );
}

function SkillBar({ value, label }: { value: number; label?: string }) {
  const tier = skillTier(value);
  const pct = Math.round((value / 20) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded bg-neutral-700 overflow-hidden">
        <div
          className="h-full rounded transition-all"
          style={{ width: `${pct}%`, backgroundColor: tier.bg }}
        />
      </div>
      {label !== undefined && (
        <span className="text-[11px] font-semibold w-24 shrink-0" style={{ color: tier.color }}>
          {tier.label}
        </span>
      )}
      <span className="text-[11px] font-bold text-neutral-400 w-5 text-right shrink-0">
        {value.toFixed(1).replace(".0", "")}
      </span>
    </div>
  );
}

// ── Overview card for one position group ─────────────────────────────────────

function OverviewCard({ group, players }: { group: PosGroup; players: SquadPlayer[] }) {
  const colors = POS_COLORS[group];

  // Compute average per skill, pick top 5 by avg value
  const skillAvgs = SKILLS.map(({ abbr, field }) => ({
    abbr,
    field,
    avg: players.length ? avg(players.map((p) => sk(p, field))) : 0,
  })).sort((a, b) => b.avg - a.avg);

  const topSkills = skillAvgs.slice(0, 5);

  return (
    <div className={`bg-neutral-900 border ${colors.border} rounded-xl p-4`}>
      <div className="flex items-center gap-2 mb-3">
        <span className={`text-xs font-bold px-2 py-0.5 rounded ${colors.badge}`}>{group}</span>
        <span className="text-xs text-neutral-400">{POS_LABEL[group]}</span>
        <span className="ml-auto text-xs text-neutral-600">{players.length} players</span>
      </div>
      {players.length === 0 ? (
        <p className="text-xs text-neutral-600">No players</p>
      ) : (
        <div className="space-y-2">
          {topSkills.map(({ abbr, field, avg: val }) => (
            <div key={field} className="flex items-center gap-2">
              <span className="text-[10px] text-neutral-500 w-7 shrink-0">{abbr}</span>
              <SkillBar value={Math.round(val * 10) / 10} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Tactical ratings panel ───────────────────────────────────────────────────

function TacticalPanel({ players }: { players: SquadPlayer[] }) {
  const metrics = useMemo(
    () =>
      TACTICAL_METRICS.map((m) => ({
        label: m.label,
        value: m.compute(players, players),
      })),
    [players]
  );

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
      <h2 className="text-sm font-bold text-neutral-300 uppercase tracking-widest mb-4">
        Advanced Tactics Ratings
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
        {metrics.map(({ label, value }) => (
          <div key={label} className="flex items-center gap-3">
            <span className="text-xs text-neutral-400 w-40 shrink-0">{label}</span>
            {value === null ? (
              <span className="text-xs text-neutral-600 italic">N/A</span>
            ) : (
              <SkillBar value={Math.round(value * 10) / 10} label="" />
            )}
            {value !== null && (
              <span
                className="text-[10px] font-semibold w-20 shrink-0"
                style={{ color: skillTier(Math.round(value)).color }}
              >
                {skillTier(Math.round(value)).label}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

type FilterTab = "All" | PosGroup;

export default function SquadClient({ players }: { players: SquadPlayer[] }) {
  const [activeTab, setActiveTab] = useState<FilterTab>("All");

  // Group all players by position for overview
  const grouped = useMemo(() => {
    const map: Record<PosGroup, SquadPlayer[]> = { GK: [], D: [], M: [], F: [] };
    players.forEach((p) => map[posGroup(p.position)].push(p));
    return map;
  }, [players]);

  // Filtered + sorted for the individual players table
  const filtered = useMemo(() => {
    const pool = activeTab === "All" ? players : grouped[activeTab];
    return [...pool].sort((a, b) => {
      const ga = POS_ORDER.indexOf(posGroup(a.position));
      const gb = POS_ORDER.indexOf(posGroup(b.position));
      return ga !== gb ? ga - gb : a.name.localeCompare(b.name);
    });
  }, [activeTab, players, grouped]);

  const tabs: FilterTab[] = ["All", "GK", "D", "M", "F"];

  const syncedAt = players[0]?.synced_at
    ? new Date(players[0].synced_at).toLocaleString("en-GB", {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : null;

  if (players.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold bg-linear-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
          Squad Analysis
        </h1>
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-10 text-center">
          <Shield size={40} className="mx-auto mb-4 text-neutral-600" />
          <p className="text-neutral-400">
            No squad data yet. Run{" "}
            <code className="text-emerald-400">python main_squad_sync.py</code> to sync your squad.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-2">
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent mb-1">
            Squad Analysis
          </h1>
          <p className="text-neutral-400 text-sm">
            {players.length} players
            {syncedAt && (
              <span className="text-neutral-600 ml-2">· Last synced {syncedAt}</span>
            )}
          </p>
        </div>
      </div>

      {/* Team Overview */}
      <section>
        <h2 className="text-xs font-bold uppercase tracking-widest text-neutral-500 mb-3">
          Team Overview — Average by Position
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {POS_ORDER.map((g) => (
            <OverviewCard key={g} group={g} players={grouped[g]} />
          ))}
        </div>
      </section>

      {/* Tactical Ratings */}
      <TacticalPanel players={players} />

      {/* Individual Players */}
      <section>
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <h2 className="text-xs font-bold uppercase tracking-widest text-neutral-500">
            Individual Players
          </h2>
          <div className="flex gap-1 ml-auto flex-wrap">
            {tabs.map((t) => (
              <button
                key={t}
                onClick={() => setActiveTab(t)}
                className={`px-3 py-1 rounded-full text-xs font-semibold border transition-colors ${
                  activeTab === t
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
                    : "bg-neutral-900 text-neutral-500 border-neutral-700 hover:border-neutral-500"
                }`}
              >
                {t === "All" ? `All (${players.length})` : `${t} (${grouped[t].length})`}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
          {/* Table header */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-neutral-800 bg-neutral-800/50">
                  <th className="text-left px-3 py-2 text-neutral-500 font-semibold uppercase tracking-wider w-16">Pos</th>
                  <th className="text-left px-3 py-2 text-neutral-500 font-semibold uppercase tracking-wider min-w-[140px]">Name</th>
                  <th className="text-center px-2 py-2 text-neutral-500 font-semibold uppercase tracking-wider w-10">Age</th>
                  <th className="text-center px-2 py-2 text-neutral-500 font-semibold uppercase tracking-wider w-20">Quality</th>
                  <th className="text-center px-2 py-2 text-neutral-500 font-semibold uppercase tracking-wider w-20">Potential</th>
                  {SKILLS.map(({ abbr }) => (
                    <th key={abbr} className="text-center px-1 py-2 text-neutral-500 font-semibold uppercase tracking-wider w-10">
                      {abbr}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((player, idx) => {
                  const group = posGroup(player.position);
                  const colors = POS_COLORS[group];
                  // Show a group header row when the group changes
                  const prevGroup = idx > 0 ? posGroup(filtered[idx - 1].position) : null;
                  const showGroupHeader = (activeTab === "All") && (prevGroup !== group);

                  return [
                    showGroupHeader && (
                      <tr key={`header-${group}`} className="bg-neutral-800/30">
                        <td colSpan={5 + SKILLS.length} className="px-3 py-1.5">
                          <span className={`text-[10px] font-bold uppercase tracking-widest ${colors.text}`}>
                            {POS_LABEL[group]}
                          </span>
                        </td>
                      </tr>
                    ),
                    <tr
                      key={player.player_id}
                      className="border-t border-neutral-800/60 hover:bg-neutral-800/30 transition-colors"
                    >
                      <td className="px-3 py-1.5">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${colors.badge}`}>
                          {player.position}
                        </span>
                      </td>
                      <td className="px-3 py-1.5 font-medium text-neutral-200 truncate max-w-[140px]">
                        {player.name}
                      </td>
                      <td className="px-2 py-1.5 text-center text-neutral-400">{player.age ?? "—"}</td>
                      <td className="px-2 py-1.5 text-center text-neutral-300 text-[10px]">
                        {player.quality ?? "—"}
                      </td>
                      <td className="px-2 py-1.5 text-center text-neutral-300 text-[10px]">
                        {player.potential ?? "—"}
                      </td>
                      {SKILLS.map(({ field }) => (
                        <td key={field} className="px-1 py-1">
                          <SkillChip value={sk(player, field)} />
                        </td>
                      ))}
                    </tr>,
                  ];
                })}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}
