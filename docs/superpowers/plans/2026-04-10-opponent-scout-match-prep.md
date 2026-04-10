# Opponent Scout × Match Prep Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich AT matchup calculations with real scouted player skills, surface scouting coverage in the Match Prep header, add a Scout Opponent trigger button, and display hidden-skill squad members below the lineup table.

**Architecture:** Server-side enrichment in `fixtures/page.tsx` cross-references `opponent_scout_results` and `players` tables before data reaches the client — zero changes to AT calculation logic. A new `/api/scout-opponent` route mirrors the existing `/api/match-prep` pattern to dispatch the `opponent_scout.yml` GitHub Actions workflow.

**Tech Stack:** Next.js 15 App Router, TypeScript, Supabase JS v2, Tailwind CSS v4, Lucide React

---

## File Map

| File | Action | Summary |
|------|--------|---------|
| `web/src/types/index.ts` | Modify line 115 | Add `"scout" \| "hidden"` to `OpponentPlayer.source` |
| `web/src/app/api/scout-opponent/route.ts` | Create | POST → GitHub Actions `opponent_scout.yml` dispatch |
| `web/src/app/fixtures/page.tsx` | Modify | Add enrichment functions + `scoutingCoverage` prop |
| `web/src/app/fixtures/FixturesClient.tsx` | Modify | Coverage badge, Scout button, hidden-skill rows, source badge styles |

---

## Task 1: Extend OpponentPlayer source type

**Files:**
- Modify: `web/src/types/index.ts:115`

- [ ] **Step 1: Update the union type**

Open `web/src/types/index.ts`. Find line 115:

```typescript
  source: "db" | "est" | "est_low"
```

Replace with:

```typescript
  source: "db" | "est" | "est_low" | "scout" | "hidden"
```

- [ ] **Step 2: Verify build passes**

```bash
cd web && pnpm build
```

Expected: no TypeScript errors. The new values are additive — nothing breaks yet.

- [ ] **Step 3: Commit**

```bash
cd web && cd ..
git add web/src/types/index.ts
git commit -m "feat(types): extend OpponentPlayer source with scout and hidden"
```

---

## Task 2: Create `/api/scout-opponent` route

**Files:**
- Create: `web/src/app/api/scout-opponent/route.ts`

- [ ] **Step 1: Create the route file**

Create `web/src/app/api/scout-opponent/route.ts` with this exact content:

```typescript
import { NextRequest, NextResponse } from "next/server"

const GITHUB_TOKEN = process.env.GITHUB_TOKEN
const GITHUB_REPO  = process.env.GITHUB_REPO

export async function POST(req: NextRequest) {
  if (!GITHUB_TOKEN || !GITHUB_REPO) {
    return NextResponse.json(
      { error: "GITHUB_TOKEN or GITHUB_REPO is not configured." },
      { status: 500 }
    )
  }

  const body = await req.json().catch(() => ({}))
  const team_id: string = (body.team_id ?? "").trim()
  const season: string  = (body.season ?? "99").trim()

  if (!team_id) {
    return NextResponse.json(
      { error: "team_id is required." },
      { status: 400 }
    )
  }

  const url = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/opponent_scout.yml/dispatches`

  const ghRes = await fetch(url, {
    method: "POST",
    headers: {
      Authorization:          `Bearer ${GITHUB_TOKEN}`,
      Accept:                 "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type":         "application/json",
    },
    body: JSON.stringify({
      ref:    "main",
      inputs: { opponent_team_id: team_id, season },
    }),
  })

  if (!ghRes.ok) {
    const detail = await ghRes.text()
    return NextResponse.json(
      { error: `GitHub API error ${ghRes.status}: ${detail}` },
      { status: 502 }
    )
  }

  return NextResponse.json(
    { ok: true, message: "Scout triggered — check back in ~2 minutes." },
    { status: 200 }
  )
}
```

- [ ] **Step 2: Verify build passes**

```bash
cd web && pnpm build
```

Expected: route compiles cleanly. No runtime test needed — it mirrors `match-prep/route.ts` exactly.

- [ ] **Step 3: Commit**

```bash
cd web && cd ..
git add web/src/app/api/scout-opponent/route.ts
git commit -m "feat(api): add /api/scout-opponent route triggering opponent_scout.yml"
```

---

## Task 3: Server-side enrichment in `fixtures/page.tsx`

**Files:**
- Modify: `web/src/app/fixtures/page.tsx`

- [ ] **Step 1: Update the import line**

Find line 2:
```typescript
import type { UpcomingFixture, FixtureAnalysis } from "@/types"
```

Replace with:
```typescript
import type { UpcomingFixture, FixtureAnalysis, OpponentPlayer } from "@/types"
```

- [ ] **Step 2: Add the `ScoutedData` type alias and `getScoutedPlayerSkills` function**

Insert this block after the closing `}` of `getMyPlayers()` (after line 71) and before the `export default` line:

```typescript
type ScoutedData = {
  name: string
  position: string
  age: number
  quality: string
  skills: Record<string, number>
}

async function getScoutedPlayerSkills(
  teamIds: string[]
): Promise<Map<string, Map<string, ScoutedData>>> {
  if (!teamIds.length) return new Map()

  const { data: scoutRows, error: scoutError } = await supabase
    .from("opponent_scout_results")
    .select("player_id, team_id, player_name, position")
    .in("team_id", teamIds)
  if (scoutError) {
    console.error("Failed to fetch opponent_scout_results:", scoutError.message)
    return new Map()
  }
  if (!scoutRows?.length) return new Map()

  const playerIds = [...new Set(scoutRows.map((r) => r.player_id))]
  const { data: playerRows, error: playerError } = await supabase
    .from("players")
    .select("id, age, quality, skills")
    .in("id", playerIds)
  if (playerError) {
    console.error("Failed to fetch players for scout enrichment:", playerError.message)
    return new Map()
  }

  const playerMap = new Map((playerRows ?? []).map((p) => [p.id, p]))

  const result = new Map<string, Map<string, ScoutedData>>()
  for (const row of scoutRows) {
    if (!result.has(row.team_id)) result.set(row.team_id, new Map())
    const pd = playerMap.get(row.player_id)
    result.get(row.team_id)!.set(row.player_id, {
      name:     row.player_name ?? "",
      position: row.position ?? "",
      age:      pd?.age ?? 0,
      quality:  pd?.quality ?? "",
      skills:   (pd?.skills as Record<string, number>) ?? {},
    })
  }
  return result
}
```

- [ ] **Step 3: Add the `enrichAnalysisMap` function**

Insert this block immediately after `getScoutedPlayerSkills` (still before `export default`):

```typescript
function enrichAnalysisMap(
  analysisMap: Record<string, FixtureAnalysis>,
  scoutedMap: Map<string, Map<string, ScoutedData>>
): {
  enrichedMap: Record<string, FixtureAnalysis>
  scoutingCoverage: Record<string, { scouted: number; total: number }>
} {
  const scoutingCoverage: Record<string, { scouted: number; total: number }> = {}
  const enrichedMap: Record<string, FixtureAnalysis> = {}

  for (const [teamId, analysis] of Object.entries(analysisMap)) {
    const teamScout = scoutedMap.get(teamId)
    if (!teamScout) {
      enrichedMap[teamId] = analysis
      continue
    }

    const lineupIds = new Set<string>()
    let scoutedCount = 0

    const enrichedPlayers: OpponentPlayer[] = (analysis.opponent_players ?? []).map((p) => {
      lineupIds.add(p.id)
      if (p.source === "db") return p
      const sd = teamScout.get(p.id)
      if (sd && Object.keys(sd.skills).length > 0) {
        scoutedCount++
        return { ...p, skills: sd.skills, source: "scout" as const }
      }
      return p
    })

    const hiddenPlayers: OpponentPlayer[] = []
    for (const [playerId, sd] of teamScout.entries()) {
      if (!lineupIds.has(playerId)) {
        hiddenPlayers.push({
          id:       playerId,
          name:     sd.name,
          position: sd.position,
          age:      sd.age,
          quality:  sd.quality,
          skills:   {},
          source:   "hidden",
        })
      }
    }

    scoutingCoverage[teamId] = { scouted: scoutedCount, total: enrichedPlayers.length }
    enrichedMap[teamId] = {
      ...analysis,
      opponent_players: [...enrichedPlayers, ...hiddenPlayers],
    }
  }

  return { enrichedMap, scoutingCoverage }
}
```

- [ ] **Step 4: Update `FixturesPage` to call enrichment and pass `scoutingCoverage`**

Replace the entire `export default async function FixturesPage()` body (lines 73–92):

```typescript
export default async function FixturesPage() {
  const season = process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "99"

  const [fixtures, rawAnalysisMap, myPlayers, myTeamName] = await Promise.all([
    getFixtures(season),
    getAllAnalyses(),
    getMyPlayers(),
    getMyTeamName(),
  ])

  const opponentTeamIds = Object.keys(rawAnalysisMap)
  const scoutedMap = await getScoutedPlayerSkills(opponentTeamIds)
  const { enrichedMap, scoutingCoverage } = enrichAnalysisMap(rawAnalysisMap, scoutedMap)

  return (
    <FixturesClient
      fixtures={fixtures}
      analysisMap={enrichedMap}
      myPlayers={myPlayers}
      season={season}
      myTeamName={myTeamName}
      scoutingCoverage={scoutingCoverage}
    />
  )
}
```

- [ ] **Step 5: Verify build passes**

```bash
cd web && pnpm build
```

Expected: TypeScript error — `FixturesClient` doesn't accept `scoutingCoverage` yet. This is expected; Task 4 will fix it. If there are other errors, fix them before continuing.

- [ ] **Step 6: Commit (after Task 4 build passes)**

Wait until Task 4 is complete and `pnpm build` passes, then commit together:

```bash
git add web/src/app/fixtures/page.tsx
git commit -m "feat(fixtures): add server-side scout enrichment and scoutingCoverage prop"
```

---

## Task 4: Update `FixturesClient.tsx` — UI and prop wiring

**Files:**
- Modify: `web/src/app/fixtures/FixturesClient.tsx`

- [ ] **Step 1: Add `Search` to lucide-react import**

Find line 4:
```typescript
import { CalendarDays, ChevronRight, RefreshCw, Shield, Zap, Activity } from "lucide-react"
```

Replace with:
```typescript
import { CalendarDays, ChevronRight, RefreshCw, Search, Shield, Zap, Activity } from "lucide-react"
```

- [ ] **Step 2: Update Props interface**

Find:
```typescript
interface Props {
  fixtures: UpcomingFixture[]
  analysisMap: Record<string, FixtureAnalysis>
  myPlayers: PlayerWithPos[]
  season: string
  myTeamName: string
}
```

Replace with:
```typescript
interface Props {
  fixtures: UpcomingFixture[]
  analysisMap: Record<string, FixtureAnalysis>
  myPlayers: PlayerWithPos[]
  season: string
  myTeamName: string
  scoutingCoverage: Record<string, { scouted: number; total: number }>
}
```

- [ ] **Step 3: Add `sourceBadge` helper function**

Insert this function after the `archetypeIcon` function (after line 66):

```typescript
function sourceBadge(source: string) {
  const styles: Record<string, string> = {
    scout:   "bg-emerald-950 text-emerald-400 border border-emerald-900/50",
    db:      "bg-emerald-500/20 text-emerald-400",
    est:     "bg-yellow-500/20 text-yellow-400",
    est_low: "bg-red-500/20 text-red-400",
    hidden:  "bg-stone-900 text-stone-500",
  }
  const label = source === "est_low" ? "EST" : source.toUpperCase()
  return (
    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${styles[source] ?? "bg-neutral-700 text-neutral-400"}`}>
      {label}
    </span>
  )
}
```

- [ ] **Step 4: Update `AnalysisPanel` props signature**

Find:
```typescript
function AnalysisPanel({
  fixture,
  analysis,
  myPlayers,
  season,
  oppId,
}: {
  fixture: UpcomingFixture
  analysis: FixtureAnalysis | null
  myPlayers: PlayerWithPos[]
  season: string
  oppId: string | null
}) {
```

Replace with:
```typescript
function AnalysisPanel({
  fixture,
  analysis,
  myPlayers,
  season,
  oppId,
  scoutingCoverage,
}: {
  fixture: UpcomingFixture
  analysis: FixtureAnalysis | null
  myPlayers: PlayerWithPos[]
  season: string
  oppId: string | null
  scoutingCoverage: Record<string, { scouted: number; total: number }>
}) {
```

- [ ] **Step 5: Add scout state variables and `handleScout` inside `AnalysisPanel`**

Find the existing state declarations at the top of `AnalysisPanel`:
```typescript
  const [triggering, setTriggering] = useState(false)
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null)
```

Replace with:
```typescript
  const [triggering, setTriggering] = useState(false)
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null)
  const [scouting, setScouting] = useState(false)
  const [scoutMsg, setScoutMsg] = useState<string | null>(null)

  const coverage = oppId ? scoutingCoverage[oppId] : undefined
```

- [ ] **Step 6: Add `handleScout` function inside `AnalysisPanel`**

Find the existing `handleTrigger` function and insert `handleScout` directly after its closing `}`:

```typescript
  async function handleScout() {
    if (!oppId) return
    setScouting(true)
    setScoutMsg(null)
    try {
      const res = await fetch("/api/scout-opponent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ team_id: oppId, season }),
      })
      const data = await res.json()
      setScoutMsg(data.message ?? data.error ?? "Unknown response")
    } catch {
      setScoutMsg("Request failed — check network.")
    } finally {
      setTimeout(() => setScouting(false), 10000)
    }
  }
```

- [ ] **Step 7: Filter hidden players from AT matchup calculation**

Find:
```typescript
  const matchups: ATMatchup[] = analysis
    ? calculateATMatchups(
        myPlayers,
        (analysis.opponent_players ?? []).map(p => ({
          position: p.position,
          skills: p.skills,
        })),
        analysis.at_patterns,
        buildOppSettings(analysis)
      )
    : []
```

Replace with:
```typescript
  const lineupPlayers = (analysis?.opponent_players ?? []).filter(p => p.source !== "hidden")
  const hiddenPlayers = (analysis?.opponent_players ?? []).filter(p => p.source === "hidden")

  const matchups: ATMatchup[] = analysis
    ? calculateATMatchups(
        myPlayers,
        lineupPlayers.map(p => ({
          position: p.position,
          skills: p.skills,
        })),
        analysis.at_patterns,
        buildOppSettings(analysis)
      )
    : []
```

- [ ] **Step 8: Add scouting coverage badge to the header**

Find in the `AnalysisPanel` return — the header `<div>` block:
```typescript
        <div>
          <h2 className="text-lg font-bold text-white">
            {fixture.home_team_name} <span className="text-neutral-500">vs</span> {fixture.away_team_name}
          </h2>
          <div className="text-sm text-neutral-400 mt-0.5">
            {formatDate(fixture.match_date)} · {fixture.match_type}
            {fixture.result && (
              <span className="ml-2">{resultBadge(fixture.result)}</span>
            )}
          </div>
        </div>
```

Replace with:
```typescript
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-lg font-bold text-white">
              {fixture.home_team_name} <span className="text-neutral-500">vs</span> {fixture.away_team_name}
            </h2>
            {coverage && coverage.scouted > 0 && (
              <span className="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-900/50 text-[10px] font-medium">
                ✓ {coverage.scouted}/{coverage.total} scouted
              </span>
            )}
          </div>
          <div className="text-sm text-neutral-400 mt-0.5">
            {formatDate(fixture.match_date)} · {fixture.match_type}
            {fixture.result && (
              <span className="ml-2">{resultBadge(fixture.result)}</span>
            )}
          </div>
        </div>
```

- [ ] **Step 9: Replace the Opponent Squad section**

Find the entire Opponent Squad block (lines 353–394):
```typescript
          {/* Opponent Squad */}
          {analysis.opponent_players?.length > 0 && (
            <div>
              <div className="text-[10px] uppercase tracking-wider text-neutral-500 mb-2">
                Opponent Squad ({analysis.opponent_players.length} players)
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-neutral-500 border-b border-neutral-700/50">
                      <th className="text-left py-1 pr-2">Pos</th>
                      <th className="text-left py-1 pr-2">Name</th>
                      <th className="text-left py-1 pr-2">Age</th>
                      <th className="text-left py-1 pr-2">Quality</th>
                      <th className="text-left py-1">Src</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.opponent_players.map((p) => (
                      <tr key={p.id} className="border-b border-neutral-800/50 hover:bg-white/5">
                        <td className="py-1 pr-2 font-mono text-cyan-400">{p.position}</td>
                        <td className="py-1 pr-2 text-neutral-200 max-w-[140px] truncate">{p.name}</td>
                        <td className="py-1 pr-2 text-neutral-400">{p.age}</td>
                        <td className="py-1 pr-2 text-neutral-300">{p.quality}</td>
                        <td className="py-1">
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                            p.source === "db"
                              ? "bg-emerald-500/20 text-emerald-400"
                              : p.source === "est"
                              ? "bg-yellow-500/20 text-yellow-400"
                              : "bg-red-500/20 text-red-400"
                          }`}>
                            {p.source.toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
```

Replace with:
```typescript
          {/* Opponent Squad */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="text-[10px] uppercase tracking-wider text-neutral-500">
                Opponent Squad
                {lineupPlayers.length > 0 && ` (${lineupPlayers.length} in lineup`}
                {hiddenPlayers.length > 0 && ` · ${hiddenPlayers.length} squad`}
                {lineupPlayers.length > 0 && ")"}
              </div>
              {oppId && (
                <button
                  onClick={handleScout}
                  disabled={scouting}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-950/60 border border-blue-900/50 text-blue-400 hover:bg-blue-900/40 transition-colors text-[10px] font-medium disabled:opacity-50"
                >
                  <Search size={10} />
                  {scouting ? "Triggering…" : "Scout Opponent"}
                </button>
              )}
            </div>
            {scoutMsg && (
              <div className="text-xs px-3 py-2 rounded-lg bg-neutral-800 text-neutral-300 border border-neutral-700 mb-2">
                {scoutMsg}
              </div>
            )}
            {lineupPlayers.length === 0 && hiddenPlayers.length === 0 ? (
              <div className="text-xs text-neutral-600 text-center py-3 border border-neutral-800 rounded-lg">
                No squad data — click Scout Opponent to fetch.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-neutral-500 border-b border-neutral-700/50">
                      <th className="text-left py-1 pr-2">Pos</th>
                      <th className="text-left py-1 pr-2">Name</th>
                      <th className="text-left py-1 pr-2">Age</th>
                      <th className="text-left py-1 pr-2">Quality</th>
                      <th className="text-left py-1">Src</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lineupPlayers.map((p) => (
                      <tr key={p.id} className="border-b border-neutral-800/50 hover:bg-white/5">
                        <td className="py-1 pr-2 font-mono text-cyan-400">{p.position}</td>
                        <td className="py-1 pr-2 text-neutral-200 max-w-[140px] truncate">{p.name}</td>
                        <td className="py-1 pr-2 text-neutral-400">{p.age}</td>
                        <td className="py-1 pr-2 text-neutral-300">{p.quality}</td>
                        <td className="py-1">{sourceBadge(p.source)}</td>
                      </tr>
                    ))}
                    {hiddenPlayers.length > 0 && (
                      <tr>
                        <td colSpan={5} className="py-2">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 border-t border-dashed border-neutral-700/50" />
                            <span className="text-[10px] text-neutral-600 whitespace-nowrap">
                              Squad · skills hidden ({hiddenPlayers.length})
                            </span>
                            <div className="flex-1 border-t border-dashed border-neutral-700/50" />
                          </div>
                        </td>
                      </tr>
                    )}
                    {hiddenPlayers.map((p) => (
                      <tr key={p.id} className="border-b border-neutral-800/30">
                        <td className="py-1 pr-2 font-mono text-neutral-500">{p.position}</td>
                        <td className="py-1 pr-2 text-neutral-500 max-w-[140px] truncate">{p.name}</td>
                        <td className="py-1 pr-2 text-neutral-600">{p.age || "—"}</td>
                        <td className="py-1 pr-2 text-neutral-600">{p.quality || "—"}</td>
                        <td className="py-1">{sourceBadge(p.source)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
```

- [ ] **Step 10: Update `FixturesClient` function signature and pass props down**

Find:
```typescript
export default function FixturesClient({ fixtures, analysisMap, myPlayers, season, myTeamName }: Props) {
```

Replace with:
```typescript
export default function FixturesClient({ fixtures, analysisMap, myPlayers, season, myTeamName, scoutingCoverage }: Props) {
```

Find where `AnalysisPanel` is rendered:
```typescript
              <AnalysisPanel
                fixture={selected}
                analysis={selectedAnalysis}
                myPlayers={myPlayers}
                season={season}
                oppId={selectedOppId}
              />
```

Replace with:
```typescript
              <AnalysisPanel
                fixture={selected}
                analysis={selectedAnalysis}
                myPlayers={myPlayers}
                season={season}
                oppId={selectedOppId}
                scoutingCoverage={scoutingCoverage}
              />
```

- [ ] **Step 11: Verify build passes**

```bash
cd web && pnpm build
```

Expected: clean build with no TypeScript errors.

- [ ] **Step 12: Manual verification in browser**

```bash
cd web && pnpm dev
```

Open `http://localhost:3000/fixtures`. Verify:
1. Opponent with prior scout data shows green `✓ N/M scouted` badge in the header
2. Lineup players with real skills show `SCOUT` badge (green)
3. Lineup players without scout data show `EST` / `EST` badges (yellow/red)
4. Dashed divider row appears when hidden squad members exist
5. Hidden squad rows render in muted gray with `HIDDEN` badge
6. `Scout Opponent` button appears in the Opponent Squad header
7. Clicking Scout Opponent disables the button for 10 seconds and shows a toast message
8. AT Matchup Analysis section still renders correctly (hidden players excluded)

- [ ] **Step 13: Commit both Task 3 and Task 4 changes**

```bash
git add web/src/app/fixtures/page.tsx web/src/app/fixtures/FixturesClient.tsx
git commit -m "feat(fixtures): integrate opponent scout data into match prep

- Enrich opponent_players with real skills from opponent_scout_results
- Add hidden-skill squad members below lineup divider
- Show scouting coverage badge in match header
- Add Scout Opponent button triggering opponent_scout.yml
- Filter hidden players from AT matchup calculations"
```
