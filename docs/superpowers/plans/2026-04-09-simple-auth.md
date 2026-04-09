# Simple Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single-password gate to the Next.js dashboard so unauthenticated visitors on Vercel are redirected to a login page.

**Architecture:** Next.js middleware reads an `auth_token` cookie on every request and redirects to `/login` if it's absent or wrong. A server action validates the submitted password against `process.env.ADMIN_PASSWORD`, sets the cookie on success, and clears it on logout.

**Tech Stack:** Next.js 16 App Router, `next/headers` cookies, `next/navigation` redirect, React 19 `useActionState`, Tailwind CSS v4, Lucide React.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `web/src/app/login/actions.ts` | `login` and `logout` server actions |
| Create | `web/src/app/login/page.tsx` | Login page shell (server component) |
| Create | `web/src/app/login/LoginClient.tsx` | Password form + error display (client component) |
| Create | `web/src/middleware.ts` | Route guard — cookie check on every request |
| Modify | `web/src/app/layout.tsx` | Add logout button to sidebar + mobile header |

---

## Task 1: Server Actions

**Files:**
- Create: `web/src/app/login/actions.ts`

- [ ] **Step 1: Create the actions file**

```typescript
// web/src/app/login/actions.ts
'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export type LoginState = { error: string } | null

export async function login(
  _prevState: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const password = formData.get('password') as string

  if (password === process.env.ADMIN_PASSWORD) {
    const cookieStore = await cookies()
    cookieStore.set('auth_token', password, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 60 * 60 * 24 * 7,
      path: '/',
    })
    redirect('/')
  }

  return { error: 'Invalid password' }
}

export async function logout(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.delete('auth_token')
  redirect('/login')
}
```

- [ ] **Step 2: Add `ADMIN_PASSWORD` to local env**

In `web/.env.local`, add:
```
ADMIN_PASSWORD=your_secure_password_here
```

(Choose a strong password — this is the only thing standing between the public and the dashboard.)

- [ ] **Step 3: Commit**

```bash
git add web/src/app/login/actions.ts
git commit -m "feat(auth): add login and logout server actions"
```

---

## Task 2: Middleware

**Files:**
- Create: `web/src/middleware.ts`

- [ ] **Step 1: Create middleware**

```typescript
// web/src/middleware.ts
import { NextRequest, NextResponse } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth_token')?.value
  const isLoginPage = request.nextUrl.pathname === '/login'

  if (isLoginPage) {
    return NextResponse.next()
  }

  if (!process.env.ADMIN_PASSWORD || token !== process.env.ADMIN_PASSWORD) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
```

- [ ] **Step 2: Verify middleware location**

The file must be at `web/src/middleware.ts` (Next.js looks for `src/middleware.ts` when using the `src/` directory). Confirm the path is correct.

- [ ] **Step 3: Commit**

```bash
git add web/src/middleware.ts
git commit -m "feat(auth): add middleware route guard"
```

---

## Task 3: Login Page

**Files:**
- Create: `web/src/app/login/page.tsx`
- Create: `web/src/app/login/LoginClient.tsx`

- [ ] **Step 1: Create the client component**

```tsx
// web/src/app/login/LoginClient.tsx
'use client'

import { useActionState } from 'react'
import { Lock } from 'lucide-react'
import { login } from './actions'
import type { LoginState } from './actions'

export default function LoginClient() {
  const [state, formAction, isPending] = useActionState<LoginState, FormData>(login, null)

  return (
    <div className="min-h-screen bg-neutral-900 flex items-center justify-center">
      <div className="bg-neutral-950 border border-neutral-800 rounded-xl p-8 w-full max-w-sm">
        <div className="flex items-center space-x-3 mb-8">
          <Lock size={24} className="text-emerald-400" />
          <h1 className="text-xl font-bold bg-linear-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            PM Dashboard
          </h1>
        </div>
        <form action={formAction} className="space-y-4">
          <div>
            <label htmlFor="password" className="block text-sm text-neutral-400 mb-2">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              autoFocus
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-emerald-500 transition-colors"
              placeholder="Enter password"
            />
          </div>
          {state?.error && (
            <p className="text-red-400 text-sm">{state.error}</p>
          )}
          <button
            type="submit"
            disabled={isPending}
            className="w-full bg-linear-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-white font-medium py-2 px-4 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isPending ? 'Signing in…' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create the page shell**

```tsx
// web/src/app/login/page.tsx
import LoginClient from './LoginClient'

export default function LoginPage() {
  return <LoginClient />
}
```

- [ ] **Step 3: Commit**

```bash
git add web/src/app/login/page.tsx web/src/app/login/LoginClient.tsx
git commit -m "feat(auth): add login page"
```

---

## Task 4: Logout Button in Layout

**Files:**
- Modify: `web/src/app/layout.tsx`

- [ ] **Step 1: Add logout import to layout**

At the top of `web/src/app/layout.tsx`, add to the existing imports:

```tsx
import { LayoutDashboard, Users, ArrowRightLeft, Bot, Swords, Shield, CalendarDays, LogOut } from 'lucide-react';
import { logout } from './login/actions';
```

- [ ] **Step 2: Add logout button to desktop sidebar**

In the `<aside>` element, after the `<nav>` block and before closing `</aside>`, add:

```tsx
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
```

- [ ] **Step 3: Add logout icon to mobile header**

In the mobile `<header>` nav, after the last icon link, add:

```tsx
              <form action={logout}>
                <button type="submit" className="text-neutral-500 hover:text-neutral-300">
                  <LogOut size={20} />
                </button>
              </form>
```

- [ ] **Step 4: Commit**

```bash
git add web/src/app/layout.tsx
git commit -m "feat(auth): add logout button to sidebar and mobile header"
```

---

## Task 5: Manual Verification

- [ ] **Step 1: Start dev server**

```bash
cd web
pnpm dev
```

- [ ] **Step 2: Verify unauthenticated redirect**

Open `http://localhost:3000`. Confirm you are redirected to `http://localhost:3000/login`.

- [ ] **Step 3: Verify wrong password**

Enter a wrong password. Confirm the error message "Invalid password" appears below the button.

- [ ] **Step 4: Verify correct password**

Enter the password from `web/.env.local`. Confirm you are redirected to the dashboard at `/`.

- [ ] **Step 5: Verify logout**

Click the "Sign Out" button in the sidebar. Confirm you are redirected to `/login` and cannot access `/` without logging in again.

- [ ] **Step 6: Verify cookie properties**

Open browser DevTools → Application → Cookies. Check `auth_token`:
- `HttpOnly`: true
- `SameSite`: Strict
- Expiry: ~7 days from now

- [ ] **Step 7: Set `ADMIN_PASSWORD` in Vercel**

In the Vercel dashboard → Project Settings → Environment Variables, add:
- Key: `ADMIN_PASSWORD`
- Value: your chosen password
- Environment: Production (+ Preview if desired)

Then redeploy. Verify the deployed site also redirects to `/login`.
