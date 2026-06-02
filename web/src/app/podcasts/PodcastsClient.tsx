"use client"

import { useState } from "react"
import { Mic, Copy, Download, X, FileText, Radio, ChevronDown, ChevronRight, Sparkles } from "lucide-react"
import type { RoundRow } from "./page"

const NLM_PROMPTS = {
  audio: {
    label: "Audio Overview",
    prompt: `มุ่งเน้นการวิเคราะห์แมตช์ไทยลีกในรูปแบบพอดแคสต์วิเคราะห์ฟุตบอล

สไตล์: พูดคุยเหมือนนักวิเคราะห์ฟุตบอลมืออาชีพ 2 คน ไม่ใช่การอ่านรายงาน

ครอบคลุมประเด็นต่อไปนี้:
1. ผลการแข่งขันที่น่าสนใจและเซอร์ไพรส์ที่สุดของรอบ
2. วิเคราะห์ยุทธวิธี — formation และ AT settings ที่ทีมเลือกใช้ ได้ผลหรือไม่
3. ผู้เล่นที่โดดเด่นและ Man of the Match แต่ละเกม
4. แนวโน้ม AT ที่ทีมต่าง ๆ มักใช้ เช่น Pressing / Marking / Counter Attack
5. ผลกระทบต่อตารางคะแนนและการแข่งขันในรอบถัดไป

ห้ามอ่านสถิติแบบแห้งๆ ให้แปลงตัวเลขเป็นการวิจารณ์เชิงลึกแทน
ใช้ภาษาไทยตลอด พูดสนุกและมีความคิดเห็น ไม่กลางๆ`,
  },
  slides: {
    label: "Slide Deck",
    prompt: `สร้างสไลด์สรุปแมตช์เดย์ไทยลีก สำหรับแชร์ให้เพื่อนในลีกดู

โครงสร้างสไลด์:
1. หน้าปก — ชื่อรอบ วันที่ จำนวนแมตช์
2. ผลการแข่งขันทุกคู่ — สกอร์ + ทีมชนะเด่น
3. ไฮไลต์ยุทธวิธี — formation ที่ทีมส่วนใหญ่ใช้ + AT flags ที่น่าสนใจ
4. Man of the Match แต่ละเกม พร้อมเหตุผลสั้น ๆ
5. สถิติน่าสนใจ — สกอร์สูงสุด, upset ที่สุด
6. มองไปข้างหน้า — คู่น่าติดตามในรอบถัดไป

สไตล์: กระชับ อ่านง่าย แต่ละสไลด์ไม่เกิน 5 bullet
ใช้ภาษาไทย เน้นข้อมูลจาก source doc เท่านั้น ห้ามแต่งเพิ่ม`,
  },
  video: {
    label: "Video Overview",
    prompt: `วิเคราะห์แมตช์เดย์ไทยลีกในรูปแบบวิดีโออธิบายเชิงยุทธวิธี

มุ่งเน้น:
1. ภาพรวมผลการแข่งขันทุกคู่ — ทีมไหนชนะ แพ้ เสมอ และสกอร์
2. อธิบาย formation และ AT settings ที่แต่ละทีมเลือกใช้ ได้ผลหรือไม่
3. ไฮไลต์ประตูสำคัญและ Man of the Match แต่ละเกม
4. AT pattern ที่โดดเด่นของรอบนี้ เช่น ทีมที่ใช้ Pressing สูง / Counter Attack
5. ผลกระทบต่อตารางคะแนนและการแข่งขันในรอบถัดไป

สไตล์: อธิบายเหมือนโค้ชวิเคราะห์ยุทธวิธีให้ทีม ใช้ภาษาไทย กระชับ มีจุดเน้นชัดเจน
เน้นข้อมูลจาก source doc เท่านั้น ห้ามแต่งเพิ่ม`,
  },
} as const

type NLMTab = keyof typeof NLM_PROMPTS

function NotebookLMCard() {
  const [open, setOpen]     = useState(false)
  const [tab, setTab]       = useState<NLMTab>("audio")
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(NLM_PROMPTS[tab].prompt).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="border border-violet-400/20 rounded-xl overflow-hidden bg-violet-400/5">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-violet-400/5 transition-colors"
      >
        <Sparkles size={16} className="text-violet-400 shrink-0" />
        <span className="text-sm font-medium text-violet-300">NotebookLM Prompts</span>
        <span className="text-xs text-neutral-600 ml-1">— copy &amp; paste into NotebookLM</span>
        <div className="flex-1" />
        {open ? <ChevronDown size={14} className="text-neutral-500" /> : <ChevronRight size={14} className="text-neutral-500" />}
      </button>

      {open && (
        <div className="border-t border-violet-400/10 px-4 pb-4 pt-3 space-y-3">
          {/* Tabs */}
          <div className="flex gap-1">
            {(Object.keys(NLM_PROMPTS) as NLMTab[]).map((key) => (
              <button
                key={key}
                onClick={() => { setTab(key); setCopied(false) }}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  tab === key
                    ? "bg-violet-400/20 text-violet-300"
                    : "text-neutral-500 hover:text-neutral-300 hover:bg-white/5"
                }`}
              >
                {NLM_PROMPTS[key].label}
              </button>
            ))}
          </div>

          <pre className="whitespace-pre-wrap text-sm text-neutral-300 font-mono leading-relaxed bg-black/30 rounded-lg p-3">
            {NLM_PROMPTS[tab].prompt}
          </pre>

          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-violet-400/10 hover:bg-violet-400/20 text-violet-300 hover:text-violet-200 transition-colors"
          >
            <Copy size={13} />
            {copied ? "Copied!" : `Copy ${NLM_PROMPTS[tab].label} Prompt`}
          </button>
        </div>
      )}
    </div>
  )
}

type ContentTab = "script" | "source"

type PodcastContent = {
  podcast_script: string | null
  source_doc: string | null
}

function competitionColor(competition: string) {
  const c = competition.toLowerCase()
  if (c.includes("cup") || c.includes("taca") || c.includes("carica") || c.includes("quarter") || c.includes("final"))
    return "text-amber-400 bg-amber-400/10 border-amber-400/30"
  if (c.includes("world"))
    return "text-purple-400 bg-purple-400/10 border-purple-400/30"
  return "text-emerald-400 bg-emerald-400/10 border-emerald-400/30"
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

export default function PodcastsClient({ rounds }: { rounds: RoundRow[] }) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [content, setContent] = useState<PodcastContent | null>(null)
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<ContentTab>("script")
  const [copied, setCopied] = useState(false)

  const selectedRound = rounds.find((r) => r.round_key === selectedKey)

  function toggleExpand(key: string) {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  async function handleSelect(roundKey: string) {
    if (roundKey === selectedKey) {
      setSelectedKey(null)
      setContent(null)
      return
    }
    setSelectedKey(roundKey)
    setContent(null)
    setLoading(true)
    setTab("script")
    try {
      const res = await fetch(`/api/podcasts/${encodeURIComponent(roundKey)}`)
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
    if (!selectedRound) return
    const suffix = `${selectedRound.competition}_${selectedRound.date}`.replace(/\s+/g, "_")
    if (tab === "script" && content?.podcast_script) {
      downloadFile(content.podcast_script, `podcast_script_${suffix}.md`)
    } else if (tab === "source" && content?.source_doc) {
      downloadFile(content.source_doc, `source_doc_${suffix}.md`)
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
          <p className="text-neutral-400 text-sm">
            {rounds.length} round{rounds.length !== 1 ? "s" : ""}
          </p>
        </div>
      </div>

      <NotebookLMCard />

      <div className="flex gap-6 items-start">
        {/* Round list */}
        <div className={`space-y-3 shrink-0 ${selectedKey ? "w-80" : "w-full max-w-2xl"}`}>
          {rounds.length === 0 && (
            <div className="text-center py-16 text-neutral-500">
              <Mic size={40} className="mx-auto mb-3 opacity-30" />
              <p>No podcast scripts yet.</p>
              <p className="text-sm mt-1">Run the pipeline after a match.</p>
            </div>
          )}

          {rounds.map((round) => {
            const isSelected = round.round_key === selectedKey
            const isOpen     = expanded.has(round.round_key)
            const colorCls   = competitionColor(round.competition)

            return (
              <div
                key={round.round_key}
                className={`rounded-xl border overflow-hidden transition-all ${
                  isSelected ? "border-amber-400/40" : "border-white/10"
                }`}
              >
                {/* Round header — click to open script */}
                <button
                  onClick={() => handleSelect(round.round_key)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                    isSelected ? "bg-amber-400/10" : "bg-white/5 hover:bg-white/8"
                  }`}
                >
                  <span className={`text-xs px-2 py-0.5 rounded-full border font-medium shrink-0 ${colorCls}`}>
                    {round.competition}
                  </span>
                  <span className="text-sm text-neutral-300 font-medium shrink-0">{round.date}</span>
                  <span className="text-xs text-neutral-600 shrink-0">
                    {round.match_summaries.length} matches
                  </span>
                  <div className="flex-1" />
                  {/* Expand match list toggle */}
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleExpand(round.round_key) }}
                    className="p-1 rounded hover:bg-white/10 text-neutral-500"
                  >
                    {isOpen
                      ? <ChevronDown size={14} />
                      : <ChevronRight size={14} />}
                  </button>
                </button>

                {/* Match list (expandable) */}
                {isOpen && (
                  <div className="divide-y divide-white/5 bg-neutral-950">
                    {round.match_summaries.map((m) => (
                      <div key={m.match_id} className="px-4 py-2 text-sm text-neutral-400">
                        <span className="font-medium text-neutral-200">{m.home}</span>
                        <span className="mx-2 text-neutral-600">{m.result}</span>
                        <span className="font-medium text-neutral-200">{m.away}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Script panel */}
        {selectedKey && (
          <div
            className="flex-1 min-w-0 bg-neutral-950 border border-white/10 rounded-xl overflow-hidden flex flex-col"
            style={{ height: "calc(100vh - 180px)" }}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/5 shrink-0">
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
                  onClick={() => { setSelectedKey(null); setContent(null) }}
                  className="p-1.5 rounded-lg hover:bg-white/10 text-neutral-500 hover:text-white transition-colors"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

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
                    ? (content.podcast_script ?? "_Script not available — re-run pipeline._")
                    : (content.source_doc ?? "_Source document not available — re-run pipeline._")}
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
