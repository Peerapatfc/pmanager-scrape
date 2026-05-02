"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Shield, RefreshCw, Bookmark, Trash2, FolderOpen, Check, X, Save } from "lucide-react";
import { skillTier } from "@/lib/skillTier";
import { SKILLS } from "@/lib/skills";
import { SkillChip } from "@/lib/SkillChip";
import { FORMATIONS } from "@/lib/formations";
import type { SquadPlayer } from "./page";

// ── Position helpers ─────────────────────────────────────────────────────────
type PosGroup = "GK" | "D" | "M" | "F";

function posGroup(position: string): PosGroup {
  const p = position.trim().toUpperCase();
  if (p.startsWith("GK")) return "GK";
  if (p.startsWith("D")) return "D";
  if (p.startsWith("M")) return "M";
  return "F";
}

// Map tactic slot position code to player position group
function tacticToGroup(tacPos: string): PosGroup {
  if (tacPos === "GK") return "GK";
  if (["LB", "CD", "RB"].includes(tacPos)) return "D";
  if (["LM", "CM", "RM"].includes(tacPos)) return "M";
  return "F"; // LF, CF, RF
}

const POS_ORDER: PosGroup[] = ["GK", "D", "M", "F"];
const POS_LABEL: Record<PosGroup, string> = {
  GK: "Goalkeepers",
  D: "Defenders",
  M: "Midfielders",
  F: "Forwards",
};
const POS_COLORS: Record<PosGroup, { badge: string; border: string; text: string }> = {
  GK: { badge: "bg-yellow-500/20 text-yellow-400",   border: "border-yellow-500/30",  text: "text-yellow-400"  },
  D:  { badge: "bg-blue-500/20 text-blue-400",       border: "border-blue-500/30",    text: "text-blue-400"    },
  M:  { badge: "bg-emerald-500/20 text-emerald-400", border: "border-emerald-500/30", text: "text-emerald-400" },
  F:  { badge: "bg-red-500/20 text-red-400",         border: "border-red-500/30",     text: "text-red-400"     },
};

// ── Skill helpers ─────────────────────────────────────────────────────────────
function sk(player: SquadPlayer, field: string): number {
  return player.skills?.[field] ?? 0;
}

function avg(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((s, v) => s + v, 0) / values.length;
}

function atRec(value: number | null): { label: string; cls: string } | null {
  if (value === null) return null;
  if (value >= 13) return { label: "✓ Enable",      cls: "text-emerald-400 bg-emerald-500/10 border-emerald-500/25" };
  if (value >= 9)  return { label: "~ Situational", cls: "text-yellow-400 bg-yellow-500/10 border-yellow-500/25" };
  return             { label: "✗ Avoid",        cls: "text-red-400 bg-red-500/10 border-red-500/25" };
}

// ── Tactical rating definitions ───────────────────────────────────────────────
interface TacticalMetric {
  label: string;
  compute: (players: SquadPlayer[]) => number | null;
}

// ── Anti-tactic: MY squad's rating at COUNTERING each opponent AT ─────────────
// Source: PManager manual section 13.
// Each formula mirrors the OPPONENT'S winning condition — the stat my squad
// needs to be HIGH to deny the opponent that condition.
//
//   vs Offside Trap    → my F's Positioning + Speed   (beat the trap line)
//   vs Pressing High   → all Speed + Passing           (deny both conditions)
//   vs Pressing Low    → all Speed + Tackling          (deny both conditions)
//   vs Counter Attack  → all Speed + Passing           (deny speed & passing)
//   vs High Balls      → all Heading + Strength        (win aerial duels)
//   vs One on Ones     → my D+M Tackling + Strength    (deny opp M+F tech+str)
//   vs Keep Stand In   → my F's Heading + Finishing    (beat opp GK ref+han)
//   vs Keep Rush Out   → my F's Heading + Technique    (beat opp GK agi+cross)
//   vs Mark Zonal      → my M+F Positioning + Speed    (beat opp D+M spd+tck)
//   vs Mark M-to-M     → my M+F Positioning + Strength (beat opp D+M str+tck)
//   vs Long Shots      → my GK Agility + my D Positioning (both conditions)
//   vs 1st Time Shots  → my GK Reflexes + my D Heading    (both conditions)

const ANTI_TACTIC_METRICS: TacticalMetric[] = [
  {
    // Opp offside trap wins if their D: Positioning > my F: Positioning
    //                                  their D: Speed     > my F: Speed
    label: "vs Offside Trap",
    compute: (all) => {
      const fwds = all.filter((p) => posGroup(p.position) === "F");
      return fwds.length ? avg(fwds.map((p) => (sk(p, "Positioning") + sk(p, "Speed")) / 2)) : null;
    },
  },
  {
    // Opp pressing-high wins if their Speed > mine AND their Passing > mine
    label: "vs Pressing – High",
    compute: (all) => avg(all.map((p) => (sk(p, "Speed") + sk(p, "Passing")) / 2)),
  },
  {
    // Opp pressing-low wins if their Speed < mine AND their Tackling > mine
    // → I need HIGH Speed (deny condition 1) + HIGH Tackling (deny condition 2)
    label: "vs Pressing – Low",
    compute: (all) => avg(all.map((p) => (sk(p, "Speed") + sk(p, "Tackling")) / 2)),
  },
  {
    // Opp counter-attack wins if their Speed > mine (main) AND their Passing > mine
    label: "vs Counter Attack",
    compute: (all) => avg(all.map((p) => (sk(p, "Speed") + sk(p, "Passing")) / 2)),
  },
  {
    // Opp high balls wins if their Heading > mine AND their Strength > mine
    label: "vs High Balls",
    compute: (all) => avg(all.map((p) => (sk(p, "Heading") + sk(p, "Strength")) / 2)),
  },
  {
    // Opp one-on-ones wins if opp M+F (Technique + Strength) > my D+M (Tackling + Strength)
    label: "vs One on Ones",
    compute: (all) => {
      const dm = all.filter((p) => ["D", "M"].includes(posGroup(p.position)));
      return dm.length ? avg(dm.map((p) => (sk(p, "Tackling") + sk(p, "Strength")) / 2)) : null;
    },
  },
  {
    // Opp keep-stand-in wins if opp GK (Reflexes + Handling) > my F (Heading + Finishing)
    // → I need my F to have HIGH Heading + HIGH Finishing
    label: "vs Keeping – Stand In",
    compute: (all) => {
      const fwds = all.filter((p) => posGroup(p.position) === "F");
      return fwds.length ? avg(fwds.map((p) => (sk(p, "Heading") + sk(p, "Finishing")) / 2)) : null;
    },
  },
  {
    // Opp keep-rush-out wins if opp GK (Agility + Crosses) > my F (Heading + Technique)
    // → I need my F to have HIGH Heading + HIGH Technique
    label: "vs Keeping – Rush Out",
    compute: (all) => {
      const fwds = all.filter((p) => posGroup(p.position) === "F");
      return fwds.length ? avg(fwds.map((p) => (sk(p, "Heading") + sk(p, "Technique")) / 2)) : null;
    },
  },
  {
    // Opp zonal marking wins if opp D+M (Speed + Tackling) > my M+F (Positioning + Speed)
    label: "vs Marking – Zonal",
    compute: (all) => {
      const mf = all.filter((p) => ["M", "F"].includes(posGroup(p.position)));
      return mf.length ? avg(mf.map((p) => (sk(p, "Positioning") + sk(p, "Speed")) / 2)) : null;
    },
  },
  {
    // Opp man-to-man wins if opp D+M (Strength + Tackling) > my M+F (Positioning + Strength)
    label: "vs Marking – Man to Man",
    compute: (all) => {
      const mf = all.filter((p) => ["M", "F"].includes(posGroup(p.position)));
      return mf.length ? avg(mf.map((p) => (sk(p, "Positioning") + sk(p, "Strength")) / 2)) : null;
    },
  },
  {
    // Opp long shots wins if opp M+F (Finishing + Technique) > my GK Agility + my D Positioning
    label: "vs Long Shots",
    compute: (all) => {
      const gks = all.filter((p) => posGroup(p.position) === "GK");
      const defs = all.filter((p) => posGroup(p.position) === "D");
      if (!gks.length || !defs.length) return null;
      const gkAgi = avg(gks.map((p) => sk(p, "Agility")));
      const dPos = avg(defs.map((p) => sk(p, "Positioning")));
      return (gkAgi + dPos) / 2;
    },
  },
  {
    // Opp 1st-time shots wins if opp F (Finishing + Heading) > my GK Reflexes + my D Heading
    label: "vs First Time Shots",
    compute: (all) => {
      const gks = all.filter((p) => posGroup(p.position) === "GK");
      const defs = all.filter((p) => posGroup(p.position) === "D");
      if (!gks.length || !defs.length) return null;
      const gkRef = avg(gks.map((p) => sk(p, "Reflexes")));
      const dHea = avg(defs.map((p) => sk(p, "Heading")));
      return (gkRef + dHea) / 2;
    },
  },
];

const TACTICAL_METRICS: TacticalMetric[] = [
  { label: "Speed",           compute: (all) => avg(all.map((p) => sk(p, "Speed"))) },
  { label: "Strength",        compute: (all) => avg(all.map((p) => sk(p, "Strength"))) },
  {
    label: "Offside Trap",
    compute: (all) => {
      const defs = all.filter((p) => posGroup(p.position) === "D");
      return defs.length ? avg(defs.map((p) => (sk(p, "Positioning") + sk(p, "Speed")) / 2)) : null;
    },
  },
  { label: "Pressing – High",   compute: (all) => avg(all.map((p) => (sk(p, "Speed") + sk(p, "Passing")) / 2)) },
  { label: "Pressing – Low",    compute: (all) => avg(all.map((p) => (sk(p, "Tackling") + (20 - sk(p, "Speed"))) / 2)) },
  { label: "Counter Attack",    compute: (all) => avg(all.map((p) => (sk(p, "Speed") + sk(p, "Passing")) / 2)) },
  { label: "High Balls",        compute: (all) => avg(all.map((p) => (sk(p, "Heading") + sk(p, "Strength")) / 2)) },
  {
    label: "One on Ones",
    compute: (all) => {
      const mf = all.filter((p) => ["M", "F"].includes(posGroup(p.position)));
      return mf.length ? avg(mf.map((p) => (sk(p, "Technique") + sk(p, "Strength")) / 2)) : null;
    },
  },
  {
    label: "Keeping – Stand In",
    compute: (all) => {
      const gks = all.filter((p) => posGroup(p.position) === "GK");
      return gks.length ? avg(gks.map((p) => (sk(p, "Reflexes") + sk(p, "Handling")) / 2)) : null;
    },
  },
  {
    label: "Keeping – Rush Out",
    compute: (all) => {
      const gks = all.filter((p) => posGroup(p.position) === "GK");
      return gks.length ? avg(gks.map((p) => (sk(p, "Agility") + sk(p, "Out of Area")) / 2)) : null;
    },
  },
  {
    label: "Marking – Zonal",
    compute: (all) => {
      const dm = all.filter((p) => ["D", "M"].includes(posGroup(p.position)));
      return dm.length ? avg(dm.map((p) => (sk(p, "Speed") + sk(p, "Tackling")) / 2)) : null;
    },
  },
  {
    label: "Marking – Man to Man",
    compute: (all) => {
      const dm = all.filter((p) => ["D", "M"].includes(posGroup(p.position)));
      return dm.length ? avg(dm.map((p) => (sk(p, "Strength") + sk(p, "Tackling")) / 2)) : null;
    },
  },
  {
    label: "Long Shots",
    compute: (all) => {
      const mf = all.filter((p) => ["M", "F"].includes(posGroup(p.position)));
      return mf.length ? avg(mf.map((p) => (sk(p, "Finishing") + sk(p, "Technique")) / 2)) : null;
    },
  },
  {
    label: "First Time Shots",
    compute: (all) => {
      const fwds = all.filter((p) => posGroup(p.position) === "F");
      return fwds.length >= 3 ? avg(fwds.map((p) => (sk(p, "Finishing") + sk(p, "Heading")) / 2)) : null;
    },
  },
];

// ── Sub-components ────────────────────────────────────────────────────────────

function SkillBar({ value }: { value: number }) {
  const tier = skillTier(value);
  const pct = Math.round((value / 20) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded bg-neutral-700 overflow-hidden">
        <div className="h-full rounded transition-all" style={{ width: `${pct}%`, backgroundColor: tier.bg }} />
      </div>
      <span className="text-[11px] font-bold text-neutral-400 w-5 text-right shrink-0">
        {value.toFixed(1).replace(".0", "")}
      </span>
    </div>
  );
}

// ── Overview card for one position group ─────────────────────────────────────

function OverviewCard({ group, players }: { group: PosGroup; players: SquadPlayer[] }) {
  const colors = POS_COLORS[group];
  const skillAvgs = SKILLS.map(({ abbr, field }) => ({
    abbr,
    field,
    avg: players.length ? avg(players.map((p) => sk(p, field))) : 0,
  })).sort((a, b) => b.avg - a.avg);

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
          {skillAvgs.slice(0, 5).map(({ abbr, field, avg: val }) => (
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

// ── Lineup builder ────────────────────────────────────────────────────────────

function LineupBuilder({
  formationIdx,
  onFormationChange,
  lineup,
  onLineupChange,
  players,
}: {
  formationIdx: number;
  onFormationChange: (idx: number) => void;
  lineup: (string | null)[];
  onLineupChange: (lineup: (string | null)[]) => void;
  players: SquadPlayer[];
}) {
  const formation = FORMATIONS[formationIdx];

  // Group slots into rows by position group (GK → D → M → F)
  const rows = useMemo(() => {
    const groups: Record<PosGroup, Array<{ index: number; tacPos: string }>> = {
      GK: [], D: [], M: [], F: [],
    };
    formation.slots.forEach((tacPos, index) => {
      groups[tacticToGroup(tacPos)].push({ index, tacPos });
    });
    return POS_ORDER.map((g) => groups[g]).filter((g) => g.length > 0);
  }, [formation]);


  const assignedIds = useMemo(
    () => new Set(lineup.filter((id): id is string => id !== null)),
    [lineup]
  );

  function handleSlotChange(slotIdx: number, playerId: string | null) {
    const next = [...lineup];
    next[slotIdx] = playerId;
    onLineupChange(next);
  }

  function handleFormationChange(idx: number) {
    onFormationChange(idx);
    onLineupChange(Array(11).fill(null));
  }

  const filledCount = assignedIds.size;
  const isComplete = filledCount === 11;

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 className="text-sm font-bold text-neutral-300 uppercase tracking-widest">
          Starting Lineup
        </h2>
        <div className="flex items-center gap-3">
          <select
            value={formationIdx}
            onChange={(e) => handleFormationChange(Number(e.target.value))}
            className="bg-neutral-800 border border-neutral-700 text-neutral-200 text-xs px-3 py-1.5 rounded-lg focus:outline-none focus:border-indigo-500"
          >
            {FORMATIONS.map((f, i) => (
              <option key={i} value={i}>{f.name}</option>
            ))}
          </select>
          {filledCount > 0 && (
            <button
              onClick={() => onLineupChange(Array(11).fill(null))}
              className="text-xs text-neutral-500 hover:text-neutral-300 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Slot rows (F → M → D → GK displayed top-to-bottom like a pitch) */}
      <div className="space-y-3">
        {[...rows].reverse().map((row, rowIdx) => {
          const group = tacticToGroup(row[0].tacPos);
          const colors = POS_COLORS[group];
          return (
            <div key={rowIdx} className="flex justify-center gap-2 flex-wrap">
              {row.map(({ index, tacPos }) => {
                const compatible = players;
                const currentId = lineup[index];
                const currentPlayer = currentId
                  ? players.find((p) => p.player_id === currentId)
                  : null;
                return (
                  <div key={index} className="flex flex-col items-center gap-1 min-w-[110px]">
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${colors.badge}`}>
                      {tacPos}
                    </span>
                    <select
                      value={currentId ?? ""}
                      onChange={(e) => handleSlotChange(index, e.target.value || null)}
                      className={`bg-neutral-800 border text-[10px] px-2 py-1 rounded-lg focus:outline-none w-[110px] truncate ${
                        currentId
                          ? "border-indigo-500/50 text-neutral-100"
                          : "border-neutral-700 text-neutral-400"
                      }`}
                    >
                      <option value="">— Pick —</option>
                      {compatible.map((p) => {
                        const isAssignedElsewhere =
                          assignedIds.has(p.player_id) && p.player_id !== currentId;
                        return (
                          <option
                            key={p.player_id}
                            value={p.player_id}
                            disabled={isAssignedElsewhere}
                          >
                            {isAssignedElsewhere ? `✓ ${p.name}` : p.name}
                          </option>
                        );
                      })}
                    </select>
                    {currentPlayer && (
                      <span className="text-[9px] text-neutral-500 truncate max-w-[110px]">
                        {currentPlayer.position}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>

      {/* Status */}
      <div className="mt-4 flex items-center justify-between">
        {isComplete ? (
          <span className="text-xs text-emerald-400 font-semibold">✓ Starting 11 selected — Advanced Tactics uses these players</span>
        ) : (
          <span className="text-xs text-neutral-600">{filledCount} / 11 selected · Advanced Tactics uses full squad until all 11 are chosen</span>
        )}
      </div>
    </div>
  );
}

// ── Tactical ratings panel ───────────────────────────────────────────────────

function TacticalPanel({
  players,
  fromLineup,
  title,
  metrics: metricDefs,
}: {
  players: SquadPlayer[];
  fromLineup: boolean;
  title: string;
  metrics: TacticalMetric[];
}) {
  const metrics = useMemo(
    () => metricDefs.map((m) => ({ label: m.label, value: m.compute(players) })),
    [metricDefs, players]
  );

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
      <div className="flex items-center gap-3 mb-4">
        <h2 className="text-sm font-bold text-neutral-300 uppercase tracking-widest">
          {title}
        </h2>
        {fromLineup ? (
          <span className="text-[10px] bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded-full">
            Starting XI
          </span>
        ) : (
          <span className="text-[10px] bg-neutral-800 text-neutral-500 border border-neutral-700 px-2 py-0.5 rounded-full">
            Full Squad
          </span>
        )}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
        {metrics.map(({ label, value }) => {
          const rec = atRec(value);
          return (
            <div key={label} className="flex items-center gap-3">
              <span className="text-xs text-neutral-400 w-40 shrink-0">{label}</span>
              {value === null ? (
                <span className="text-xs text-neutral-600 italic">N/A</span>
              ) : (
                <>
                  <SkillBar value={Math.round(value * 10) / 10} />
                  <span
                    className="text-[10px] font-semibold w-20 shrink-0"
                    style={{ color: skillTier(Math.round(value)).color }}
                  >
                    {skillTier(Math.round(value)).label}
                  </span>
                  {rec && (
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border shrink-0 ${rec.cls}`}>
                      {rec.label}
                    </span>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Saved lineups types + panel ───────────────────────────────────────────────

interface SavedLineup {
  id: string;
  name: string;
  formation_idx: number;
  lineup: (string | null)[];
  saved_at: string;
}

function SavedLineupsPanel({
  saves,
  activeSaveId,
  loading,
  onLoad,
  onDelete,
  onSave,
  onUpdate,
}: {
  saves: SavedLineup[];
  activeSaveId: string | null;
  loading: boolean;
  onLoad: (s: SavedLineup) => void;
  onDelete: (id: string) => void;
  onSave: (name: string) => Promise<void>;
  onUpdate: (id: string) => Promise<void>;
}) {
  const [inputVisible, setInputVisible] = useState(false);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function openInput() {
    setName(`Lineup ${saves.length + 1}`);
    setInputVisible(true);
    setTimeout(() => { inputRef.current?.focus(); inputRef.current?.select(); }, 0);
  }

  async function handleConfirm() {
    const trimmed = name.trim();
    if (!trimmed) return;
    setSaving(true);
    await onSave(trimmed);
    setSaving(false);
    setInputVisible(false);
    setName("");
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") handleConfirm();
    if (e.key === "Escape") { setInputVisible(false); setName(""); }
  }

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <h2 className="text-sm font-bold text-neutral-300 uppercase tracking-widest flex items-center gap-2">
          <Bookmark size={13} className="text-amber-400" />
          Saved Lineups
          {saves.length > 0 && (
            <span className="text-[10px] font-normal text-neutral-500">({saves.length})</span>
          )}
        </h2>

        {inputVisible ? (
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Lineup name…"
              className="bg-neutral-800 border border-indigo-500/60 text-neutral-100 text-xs px-3 py-1.5 rounded-lg focus:outline-none w-44"
            />
            <button
              onClick={handleConfirm}
              disabled={!name.trim() || saving}
              className="p-1.5 rounded-lg bg-indigo-500/20 border border-indigo-500/40 text-indigo-400 hover:bg-indigo-500/30 disabled:opacity-40 transition-colors"
            >
              <Check size={12} />
            </button>
            <button
              onClick={() => { setInputVisible(false); setName(""); }}
              className="p-1.5 rounded-lg bg-neutral-800 border border-neutral-700 text-neutral-500 hover:text-neutral-300 transition-colors"
            >
              <X size={12} />
            </button>
          </div>
        ) : (
          <button
            onClick={openInput}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold hover:bg-indigo-500/20 transition-colors"
          >
            <Bookmark size={12} />
            Save current lineup
          </button>
        )}
      </div>

      {loading ? (
        <p className="text-xs text-neutral-600 italic">Loading…</p>
      ) : saves.length === 0 ? (
        <p className="text-xs text-neutral-600 italic">No saved lineups yet.</p>
      ) : (
        <div className="space-y-2">
          {saves.map((s) => {
            const isActive = s.id === activeSaveId;
            const savedDate = new Date(s.saved_at).toLocaleString("en-GB", {
              dateStyle: "short",
              timeStyle: "short",
            });
            return (
              <div
                key={s.id}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-colors ${
                  isActive
                    ? "bg-indigo-900/20 border-indigo-500/40"
                    : "bg-neutral-800/40 border-neutral-800 hover:border-neutral-700"
                }`}
              >
                {isActive && <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />}
                <div className="flex-1 min-w-0">
                  <span className={`text-xs font-semibold truncate block ${isActive ? "text-indigo-300" : "text-neutral-200"}`}>
                    {s.name}
                  </span>
                  <span className="text-[10px] text-neutral-500">
                    {FORMATIONS[s.formation_idx]?.name ?? "—"} · {savedDate}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  {isActive ? (
                    <span className="text-[10px] text-indigo-400 font-semibold px-2">Active</span>
                  ) : (
                    <button
                      onClick={() => onLoad(s)}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-neutral-700 border border-neutral-600 text-neutral-300 text-[10px] font-semibold hover:bg-neutral-600 transition-colors"
                    >
                      <FolderOpen size={11} />
                      Load
                    </button>
                  )}
                  <button
                    onClick={() => onUpdate(s.id)}
                    title="Overwrite with current lineup"
                    className="p-1.5 rounded-lg text-neutral-600 hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors"
                  >
                    <Save size={11} />
                  </button>
                  <button
                    onClick={() => onDelete(s.id)}
                    className="p-1.5 rounded-lg text-neutral-600 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

type FilterTab = "All" | PosGroup;

export default function SquadClient({ players }: { players: SquadPlayer[] }) {
  const [activeTab, setActiveTab] = useState<FilterTab>("All");
  const [formationIdx, setFormationIdx] = useState(17); // default: 4-4-2
  const [lineup, setLineup] = useState<(string | null)[]>(Array(11).fill(null));
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  // ── Saved lineups state ──────────────────────────────────────────────────────
  const [saves, setSaves] = useState<SavedLineup[]>([]);
  const [activeSaveId, setActiveSaveId] = useState<string | null>(null);
  const [savesLoading, setSavesLoading] = useState(true);

  useEffect(() => {
    fetch("/api/saved-lineups")
      .then((r) => r.json())
      .then((data: SavedLineup[]) => setSaves(Array.isArray(data) ? data : []))
      .catch(() => setSaves([]))
      .finally(() => setSavesLoading(false));
  }, []);

  async function handleSaveLineup(name: string) {
    const res = await fetch("/api/saved-lineups", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, formation_idx: formationIdx, lineup }),
    });
    if (!res.ok) return;
    const saved: SavedLineup = await res.json();
    setSaves((prev) => [saved, ...prev]);
    setActiveSaveId(saved.id);
  }

  function handleLoadLineup(s: SavedLineup) {
    setFormationIdx(s.formation_idx);
    setLineup(s.lineup);
    setActiveSaveId(s.id);
  }

  async function handleDeleteLineup(id: string) {
    await fetch(`/api/saved-lineups/${id}`, { method: "DELETE" });
    setSaves((prev) => prev.filter((s) => s.id !== id));
    if (activeSaveId === id) setActiveSaveId(null);
  }

  async function handleUpdateLineup(id: string) {
    const res = await fetch(`/api/saved-lineups/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ formation_idx: formationIdx, lineup }),
    });
    if (!res.ok) return;
    const updated: SavedLineup = await res.json();
    setSaves((prev) => prev.map((s) => (s.id === id ? updated : s)));
    setActiveSaveId(id);
  }

  // Clear active save when user manually changes the lineup/formation
  function handleFormationChange(idx: number) {
    setFormationIdx(idx);
    setActiveSaveId(null);
  }

  function handleLineupChange(next: (string | null)[]) {
    setLineup(next);
    setActiveSaveId(null);
  }

  async function handleSync() {
    setSyncing(true);
    setSyncMsg(null);
    try {
      const res = await fetch("/api/squad-sync", { method: "POST" });
      const data = await res.json();
      setSyncMsg(data.message ?? data.error ?? "Done");
    } catch {
      setSyncMsg("Failed to trigger sync.");
    } finally {
      setSyncing(false);
    }
  }

  // Resolve starting eleven from lineup assignments
  const startingEleven = useMemo(() => {
    const result: SquadPlayer[] = [];
    lineup.forEach((id) => {
      if (!id) return;
      const p = players.find((pl) => pl.player_id === id);
      if (p) result.push(p);
    });
    return result;
  }, [lineup, players]);

  const isLineupComplete = startingEleven.length === 11;

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
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent mb-1">
            Squad Analysis
          </h1>
          <p className="text-neutral-400 text-sm">
            {players.length} players
            {syncedAt && <span className="text-neutral-600 ml-2">· Last synced {syncedAt}</span>}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold hover:bg-emerald-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw size={13} className={syncing ? "animate-spin" : ""} />
            {syncing ? "Syncing…" : "Sync Squad"}
          </button>
          {syncMsg && (
            <span className="text-[11px] text-neutral-500">{syncMsg}</span>
          )}
        </div>
      </div>

      {/* Lineup Builder */}
      <LineupBuilder
        formationIdx={formationIdx}
        onFormationChange={handleFormationChange}
        lineup={lineup}
        onLineupChange={handleLineupChange}
        players={players}
      />

      {/* Saved Lineups */}
      <SavedLineupsPanel
        saves={saves}
        activeSaveId={activeSaveId}
        loading={savesLoading}
        onLoad={handleLoadLineup}
        onDelete={handleDeleteLineup}
        onSave={handleSaveLineup}
        onUpdate={handleUpdateLineup}
      />

      {/* Team Overview — always full squad */}
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

      {/* Tactical Ratings — starting XI if complete, else full squad */}
      <TacticalPanel
        title="Advanced Tactics Ratings"
        metrics={TACTICAL_METRICS}
        players={isLineupComplete ? startingEleven : players}
        fromLineup={isLineupComplete}
      />

      {/* Anti-Tactic Ratings — counters to each opponent tactic */}
      <TacticalPanel
        title="Anti-Tactic Ratings"
        metrics={ANTI_TACTIC_METRICS}
        players={isLineupComplete ? startingEleven : players}
        fromLineup={isLineupComplete}
      />

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
                  const prevGroup = idx > 0 ? posGroup(filtered[idx - 1].position) : null;
                  const showGroupHeader = activeTab === "All" && prevGroup !== group;
                  const isStarter = isLineupComplete && startingEleven.some((p) => p.player_id === player.player_id);

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
                      className={`border-t border-neutral-800/60 transition-colors ${
                        isStarter
                          ? "bg-indigo-900/10 hover:bg-indigo-900/20"
                          : "hover:bg-neutral-800/30"
                      }`}
                    >
                      <td className="px-3 py-1.5">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${colors.badge}`}>
                          {player.position}
                        </span>
                      </td>
                      <td className="px-3 py-1.5 font-medium text-neutral-200 truncate max-w-[140px]">
                        <span className="flex items-center gap-1.5">
                          {isStarter && (
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                          )}
                          {player.name}
                        </span>
                      </td>
                      <td className="px-2 py-1.5 text-center text-neutral-400">{player.age ?? "—"}</td>
                      <td className="px-2 py-1.5 text-center text-neutral-300 text-[10px]">{player.quality ?? "—"}</td>
                      <td className="px-2 py-1.5 text-center text-neutral-300 text-[10px]">{player.potential ?? "—"}</td>
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
