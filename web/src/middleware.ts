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
