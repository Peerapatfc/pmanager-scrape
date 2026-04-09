# Simple Auth — Design Spec

**Date:** 2026-04-09
**Scope:** Add password-gate authentication to the Next.js dashboard on Vercel for a single user.

---

## Problem

The dashboard is deployed publicly on Vercel. Any person who finds the URL can view all data. A lightweight auth layer is needed to restrict access to the owner only.

---

## Approach

Middleware password gate — no new packages. A single `ADMIN_PASSWORD` environment variable is set on Vercel. Every request passes through Next.js middleware which checks for a valid `auth_token` cookie. If absent, the user is redirected to `/login`. On successful login, the cookie is set and the user is redirected to the dashboard.

---

## Architecture

### Request Flow

```
Request → middleware.ts
  ├── path is /login → pass through
  └── cookie "auth_token" missing or wrong → redirect to /login

POST /login (Server Action)
  ├── password === process.env.ADMIN_PASSWORD → set cookie → redirect to /
  └── password !== ADMIN_PASSWORD → return { error: "Invalid password" }

Logout (Server Action)
  └── clear cookie → redirect to /login
```

### New Files

| File | Purpose |
|------|---------|
| `web/src/middleware.ts` | Route guard — checks cookie on every non-login request |
| `web/src/app/login/page.tsx` | Server component — login page shell |
| `web/src/app/login/LoginClient.tsx` | Client component — password form + Server Actions |

### Modified Files

| File | Change |
|------|--------|
| `web/src/app/layout.tsx` | Add logout button to sidebar (bottom) and mobile header |

---

## Cookie

| Property | Value |
|----------|-------|
| Name | `auth_token` |
| Value | The raw `ADMIN_PASSWORD` string |
| `httpOnly` | `true` — not accessible via JS |
| `secure` | `true` — HTTPS only (Vercel always uses HTTPS) |
| `sameSite` | `strict` |
| Expiry | 7 days (`maxAge: 60 * 60 * 24 * 7`) |

Validation: middleware reads the cookie value and compares it to `process.env.ADMIN_PASSWORD`. Equal = authenticated.

---

## Environment Variables

| Variable | Where | Notes |
|----------|-------|-------|
| `ADMIN_PASSWORD` | `web/.env.local` (local) + Vercel dashboard (production) | Never commit to git |

---

## UI — Login Page

- Full-screen layout: `bg-neutral-900 flex items-center justify-center min-h-screen`
- Centered card: `bg-neutral-950 border border-neutral-800 rounded-xl p-8 w-full max-w-sm`
- "PM Dashboard" gradient title matching existing layout (`from-emerald-400 to-cyan-400`)
- Password `<input>` field (type=password) with dark styling matching existing inputs
- "Sign In" button using existing emerald/cyan gradient style
- Error message below button in red (`text-red-400`) if password is wrong
- Logout button at the bottom of the sidebar in layout.tsx (desktop) and in the mobile header

---

## Security Notes

- `httpOnly` prevents XSS from stealing the cookie
- `secure` ensures the cookie is only sent over HTTPS
- Vercel always serves over HTTPS in production
- Password rotation: update `ADMIN_PASSWORD` in Vercel env vars and redeploy — existing cookie becomes invalid immediately (comparison will fail)
- No rate limiting needed for a personal tool, but Vercel's built-in edge protection applies

---

## Out of Scope

- Multiple users / user management
- OAuth / social login
- JWT / session tokens
- Rate limiting on the login form
