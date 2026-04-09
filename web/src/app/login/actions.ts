'use server'

import { timingSafeEqual } from 'crypto'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export type LoginState = { error: string } | null

export async function login(
  _prevState: LoginState,
  formData: FormData,
): Promise<LoginState> {
  const password = formData.get('password')
  if (typeof password !== 'string' || !password) {
    return { error: 'Invalid password' }
  }

  const adminPassword = process.env.ADMIN_PASSWORD
  if (
    adminPassword &&
    timingSafeEqual(Buffer.from(password), Buffer.from(adminPassword))
  ) {
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
