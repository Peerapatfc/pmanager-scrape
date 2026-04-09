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
