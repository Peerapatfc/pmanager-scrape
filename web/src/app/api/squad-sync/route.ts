import { NextResponse } from "next/server"

const GITHUB_TOKEN = process.env.GITHUB_TOKEN
const GITHUB_REPO  = process.env.GITHUB_REPO

export async function POST() {
  if (!GITHUB_TOKEN || !GITHUB_REPO) {
    return NextResponse.json(
      { error: "GITHUB_TOKEN or GITHUB_REPO is not configured." },
      { status: 500 }
    )
  }

  const url = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/squad_sync.yml/dispatches`

  const ghRes = await fetch(url, {
    method: "POST",
    headers: {
      Authorization:          `Bearer ${GITHUB_TOKEN}`,
      Accept:                 "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type":         "application/json",
    },
    body: JSON.stringify({ ref: "main" }),
  })

  if (!ghRes.ok) {
    const detail = await ghRes.text()
    return NextResponse.json(
      { error: `GitHub API error ${ghRes.status}: ${detail}` },
      { status: 502 }
    )
  }

  return NextResponse.json(
    { ok: true, message: "Squad sync triggered — check back in ~2 minutes." },
    { status: 200 }
  )
}
