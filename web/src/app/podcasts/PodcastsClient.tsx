"use client"

import { useState } from "react"
import { Mic, Copy, Download, X, FileText, Radio, ChevronRight } from "lucide-react"
import type { PodcastRow } from "./page"

type ContentTab = "script" | "source"

type PodcastContent = {
  podcast_script: string | null
  source_doc: string | null
}

function parsePath(path: string | null) {
  if (!path) return { date: "—", competition: "—", home: "—", away: "—" }
  const parts = path.replace(/\\/g, "/").split("/")
  const date = parts.at(-3) ?? "—"
  const competition = (parts.at(-2) ?? "—").replace(/_/g, " ")
  const matchupRaw = parts.at(-1) ?? ""
  const vsIdx = matchupRaw.indexOf("_vs_")
  const home = vsIdx !== -1 ? matchupRaw.slice(0, vsIdx).replace(/_/g, " ") : matchupRaw
  const away = vsIdx !== -1 ? matchupRaw.slice(vsIdx + 4).replace(/_/g, " ") : "—"
  return { date, competition, home, away }
}

function competitionColor(competition: string) {
  const c = competition.toLowerCase()
  if (c.includes("cup") || c.includes("taca") || c.includes("carica")) return "text-amber-400 bg-amber-400/10 border-amber-400/20"
  if (c.includes("world")) return "text-purple-400 bg-purple-400/10 border-purple-400/20"
  return "text-emerald-400 bg-emerald-400/10 border-emerald-400/20"
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {})
}

function downloadFile(text: string, filename: string) {
  const blob = new Blob([text], { type: "text/markdown" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function PodcastsClient({ podcasts }: { podcasts: PodcastRow[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [content, setContent] = useState<PodcastContent | null>(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<ContentTab>("script")
  const [copied, setCopied] = useState(false)

  const selectedPodcast = podcasts.find((p) => p.match_id === selectedId)

  async function handleSelect(matchId: string) {
    if (matchId === selectedId) {
      setSelectedId(null)
      setContent(null)
      return
    }
    setSelectedId(matchId)
    setContent(null)
    setLoading(true)
    setTab("script")
    try {
      const res = await fetch(`/api/podcasts/${matchId}`)
      const json = await res.json()
      setContent(json)
    } catch {
      setContent(null)
    } finally {
      setLoading(false)
    }
  }

  function handleCopy() {
    const text = tab === "script" ? content?.podcast_script : content?.source_doc
    if (!text) return
    copyToClipboard(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function handleDownload() {
    const { home, away, date } = parsePath(selectedPodcast?.podcast_path ?? null)
    if (tab === "script" && content?.podcast_script) {
      downloadFile(content.podcast_script, `podcast_script_${home}_vs_${away}_${date}.md`)
    } else if (tab === "source" && content?.source_doc) {
      downloadFile(content.source_doc, `source_doc_${home}_vs_${away}_${date}.md`)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-amber-400/10">
          <Mic className="text-amber-400" size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Podcast Scripts</h1>
          <p className="text-neutral-400 text-sm">{podcasts.length} match{podcasts.length !== 1 ? "es" : ""} processed</p>
        </div>
      </div>

      <div className="flex gap-6 items-start">
        {/* List */}
        <div className={`space-y-3 flex-shrink-0 ${selectedId ? "w-80" : "w-full max-w-2xl"}`}>
          {podcasts.length === 0 && (
            <div className="text-center py-16 text-neutral-500">
              <Mic size={40} className="mx-auto mb-3 opacity-30" />
              <p>No podcast scripts yet.</p>
              <p className="text-sm mt-1">Run the pipeline after a match.</p>
            </div>
          )}
          {podcasts.map((p) => {
            const { date, competition, home, away } = parsePath(p.podcast_path)
            const isSelected = p.match_id === selectedId
            const score =
              p.home_score != null && p.away_score != null
                ? `${p.home_score} - ${p.away_score}`
                : "? - ?"

            return (
              <button
                key={p.match_id}
                onClick={() => handleSelect(p.match_id)}
                className={`w-full text-left p-4 rounded-xl border transition-all ${
                  isSelected
                    ? "bg-amber-400/10 border-amber-400/40"
                    : "bg-white/5 border-white/10 hover:bg-white/8 hover:border-white/20"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${competitionColor(competition)}`}>
                        {competition}
                      </span>
                      <span className="text-xs text-neutral-500">{date}</span>
                    </div>
                    <div className="font-semibold text-white truncate">
                      {home} <span className="text-neutral-400 font-normal">{score}</span> {away}
                    </div>
                  </div>
                  <ChevronRight
                    size={16}
                    className={`flex-shrink-0 mt-1 transition-transform text-neutral-500 ${isSelected ? "rotate-90 text-amber-400" : ""}`}
                  />
                </div>
              </button>
            )
          })}
        </div>

        {/* Detail panel */}
        {selectedId && (
          <div className="flex-1 min-w-0 bg-neutral-950 border border-white/10 rounded-xl overflow-hidden flex flex-col" style={{ height: "calc(100vh - 180px)" }}>
            {/* Panel header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/5 flex-shrink-0">
              {/* Tabs */}
              <div className="flex gap-1">
                <button
                  onClick={() => setTab("script")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    tab === "script" ? "bg-amber-400/20 text-amber-400" : "text-neutral-400 hover:text-white"
                  }`}
                >
                  <Radio size={14} />
                  Podcast Script
                </button>
                <button
                  onClick={() => setTab("source")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    tab === "source" ? "bg-blue-400/20 text-blue-400" : "text-neutral-400 hover:text-white"
                  }`}
                >
                  <FileText size={14} />
                  Source Doc
                </button>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                {content && (
                  <>
                    <button
                      onClick={handleCopy}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-white/5 hover:bg-white/10 text-neutral-300 hover:text-white transition-colors"
                    >
                      <Copy size={14} />
                      {copied ? "Copied!" : "Copy"}
                    </button>
                    <button
                      onClick={handleDownload}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-white/5 hover:bg-white/10 text-neutral-300 hover:text-white transition-colors"
                    >
                      <Download size={14} />
                      Download
                    </button>
                  </>
                )}
                <button
                  onClick={() => { setSelectedId(null); setContent(null) }}
                  className="p-1.5 rounded-lg hover:bg-white/10 text-neutral-500 hover:text-white transition-colors"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-4">
              {loading && (
                <div className="flex items-center justify-center h-full text-neutral-500">
                  <div className="text-center">
                    <div className="w-8 h-8 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-sm">Loading script...</p>
                  </div>
                </div>
              )}
              {!loading && content && (
                <pre className="whitespace-pre-wrap text-sm text-neutral-200 font-mono leading-relaxed">
                  {tab === "script"
                    ? (content.podcast_script ?? "_Script not available_")
                    : (content.source_doc ?? "_Source document not available_")}
                </pre>
              )}
              {!loading && !content && (
                <div className="flex items-center justify-center h-full text-neutral-600">
                  <p className="text-sm">Failed to load content.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
