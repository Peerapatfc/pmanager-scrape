# Opponent Scout × Match Prep Integration

**Date:** 2026-04-10  
**Status:** Approved  
**Author:** Brainstorming session

---

## Problem

`fixture_analysis.opponent_players` currently contains estimated skills (`source: "est"` or `"est_low"`) even when the user has already run the Opponent Scout workflow for that team. Real skill data exists in the `players` table but is never used to improve AT matchup accuracy.

Additionally, the Match Prep panel shows no indication of whether an opponent has been scouted, and there is no way to trigger a new scout run from within the Match Prep UI.

---

## Goals

1. **Enrich** estimated opponent player skills with real data from prior scout runs → improve AT matchup accuracy automatically
2. **Surface** scouting coverage (e.g. "3/20 scouted") as a badge next to the opponent name
3. **Enable** triggering a new opponent scout run directly from Match Prep via a "Scout Opponent" button
4. **Display** all known squad members (even those with hidden skills) below the lineup in the Opponent Squad section

---

## Out of Scope

- Cohort-average estimation for remaining `est` players (separate feature, separate spec)
- Any changes to the AT calculation logic itself
- Changes to `match_prep.py` or any Python scraper

---

## Architecture

All enrichment happens **server-side** in `fixtures/page.tsx` before the client receives data. The client receives a richer `analysisMap` and a new `scoutingCoverage` prop — zero changes to AT calculation logic in `atCalculations.ts`.

```
fixtures/page.tsx (server)
  ├── getScoutedPlayerSkills(teamIds)   ← 2 new DB queries
  ├── enrichAnalysisMap()               ← merges scout data in-memory
  └── → FixturesClient (props)
         ├── analysisMap (enriched)
         └── scoutingCoverage           ← NEW prop
```

---

## Data Flow

### New queries in `fixtures/page.tsx`

**`getScoutedPlayerSkills(teamIds: string[])`**

```
Step 1: SELECT player_id, team_id, player_name, position
        FROM opponent_scout_results
        WHERE team_id IN (:teamIds)

Step 2: SELECT id, name, age, quality, skills
        FROM players
        WHERE id IN (:playerIds from step 1)

Returns: Map<teamId, Map<playerId, { name, position, age?, quality?, skills? }>>
```

**`enrichAnalysisMap(analysisMap, scoutedSkillsMap)`**

For each `FixtureAnalysis` in `analysisMap`:

1. For each `opponent_player` where `source !== "db"`:
   - If `player.id` found in scouted skills → replace `skills`, set `source = "scout"`
   - Otherwise → leave as-is (`est` / `est_low`)

2. Collect squad players (in `opponent_scout_results` for this team but NOT in `opponent_players`):
   - `name` + `position` come from `opponent_scout_results`
   - `age` + `quality` come from `players` table if the player exists there; otherwise left as defaults (`age: 0, quality: ""`)
   - Append to `opponent_players` with `source = "hidden"` and `skills = {}`
   - These are display-only and excluded from AT calculations by the existing filter logic

3. Compute `scoutingCoverage`:
   ```
   scouted = count of opponent_players with source === "scout"
   total   = count of opponent_players (excluding hidden)
   → Record<teamId, { scouted: number; total: number }>
   ```

### Props passed to FixturesClient

```typescript
// Existing (unchanged)
fixtures: UpcomingFixture[]
analysisMap: Record<string, FixtureAnalysis>   // now enriched
myPlayers: PlayerWithPos[]
myTeamName: string

// New
scoutingCoverage: Record<string, { scouted: number; total: number }>
```

---

## Type Changes

**File:** `web/src/types/index.ts`

```typescript
// Before
source: "db" | "est" | "est_low"

// After
source: "db" | "est" | "est_low" | "scout" | "hidden"
```

| Value | Meaning | Used in AT calcs |
|-------|---------|-----------------|
| `"db"` | Player in our `players` table (seen on transfer market) | Yes |
| `"est"` | match_prep estimated skills (medium confidence) | Yes |
| `"est_low"` | match_prep estimated skills (low confidence) | Yes |
| `"scout"` | Real skills from `opponent_scout_results` + `players` (enriched) | Yes |
| `"hidden"` | In squad; skills not visible (not on transfer list) | **No** |

---

## UI Changes

**File:** `web/src/app/fixtures/FixturesClient.tsx`

### 1. Scouting coverage badge

Location: Match Prep panel header, next to opponent team name.

```
1stQueue vs FC Novi Beograd  [✓ 3/20 scouted]
```

- Badge only shown when `scoutingCoverage[oppTeamId].scouted > 0`
- Hidden when no scouting data exists for the opponent
- Style: `bg-emerald-950 text-emerald-400 border border-emerald-900` pill

### 2. Opponent Squad table — source badges

| Source | Badge text | Style |
|--------|-----------|-------|
| `"scout"` | `scout` | `bg-emerald-950 text-emerald-400` |
| `"est"` | `est` | `bg-slate-900 text-blue-300` |
| `"est_low"` | `est` | same as `est` |
| `"db"` | `db` | `bg-slate-900 text-slate-400` |
| `"hidden"` | `hidden` | `bg-stone-900 text-stone-500` |

### 3. Hidden-skill players divider

After all lineup players (source ≠ `"hidden"`), render a dashed divider row:

```
— — — — Squad · skills hidden (N) — — — —
```

Then list hidden-skill players below in muted styling. QUALITY and AGE are shown if the player exists in the `players` table; otherwise those cells are blank. SKILLS column is omitted for hidden rows.

### 4. Scout Opponent button

Location: `OPPONENT SQUAD` section header, right side.

**Behavior:**
1. User clicks → POST `/api/scout-opponent` with `{ team_id, season }`
2. Button disables immediately (prevents double-trigger)
3. On success → show toast: `"Scout triggered — check back in ~2 minutes"`
4. Button re-enables after 10 seconds
5. On failure → show error toast with status message

---

## New API Route

**File:** `web/src/app/api/scout-opponent/route.ts`

```
POST /api/scout-opponent
Body: { team_id: string; season: string }

→ Triggers GitHub Actions workflow: opponent_scout.yml
  (same dispatch pattern as /api/match-prep/route.ts)
  inputs: { opponent_team_id: team_id, season }

Response 200: { ok: true, message: "Scout triggered — check back in ~2 minutes." }
Response 4xx: { ok: false, error: "..." }
```

Mirrors the existing pattern in `/api/match-prep/route.ts` — same auth header, same `workflow_dispatch` event, different workflow filename and inputs.

---

## Files Changed

| File | Change type | Summary |
|------|------------|---------|
| `web/src/types/index.ts` | Modify | Add `"scout" \| "hidden"` to `OpponentPlayer.source` |
| `web/src/app/fixtures/page.tsx` | Modify | Add `getScoutedPlayerSkills()`, `enrichAnalysisMap()`, pass `scoutingCoverage` prop |
| `web/src/app/fixtures/FixturesClient.tsx` | Modify | Coverage badge, source badge styling, hidden-skill rows, Scout button + toast |
| `web/src/app/api/scout-opponent/route.ts` | Create | POST endpoint → GitHub Actions `opponent_scout.yml` dispatch |

**No changes to:**
- `web/src/lib/atCalculations.ts` — hidden players excluded upstream
- `match_prep.py` or any Python scraper
- Supabase schema

---

## AT Calculation Correctness

Hidden-skill players (`source === "hidden"`) are appended to `opponent_players` for display. The AT calculation call in `FixturesClient.tsx` passes `oppPlayers` filtered to only those with real/estimated skills — hidden players are excluded before reaching `calculateATMatchups()`.

This filter must be explicit:
```typescript
const oppPlayersForAT = analysis.opponent_players.filter(p => p.source !== "hidden")
```

---

## Edge Cases

| Scenario | Behavior |
|----------|---------|
| Opponent never scouted | No badge shown; all players show `est`/`db` as before |
| Scout ran but player IDs don't match lineup | No enrichment; stays `est` |
| `opponent_scout_results` has player but `players` table has no skills | No enrichment; stays `est` (skills = null) |
| GitHub Actions dispatch fails (no token) | Toast shows error; button re-enables |
| `season` unknown for fixture | Use fixture's `season` field from `UpcomingFixture` |
