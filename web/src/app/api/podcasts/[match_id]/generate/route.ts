import { createClient } from "@supabase/supabase-js"
import { NextResponse } from "next/server"
import { join } from "path"
import { readFileSync } from "fs"

function db() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_KEY!,
  )
}

const MANUAL_DIR = join(process.cwd(), "..", "docs", "manual", "sections")
const MANUAL_FILES = ["section_13.md", "section_14.md", "section_34.md", "section_20.md"]
const MAX_SECTION_CHARS = 3000

function loadRulesContext(): string {
  const parts: string[] = []
  for (const fname of MANUAL_FILES) {
    try {
      let content = readFileSync(join(MANUAL_DIR, fname), "utf-8")
      if (content.length > MAX_SECTION_CHARS) {
        content = content.slice(0, MAX_SECTION_CHARS).replace(/\n[^\n]*$/, "")
      }
      parts.push(content)
    } catch {
      // file not found — skip
    }
  }
  return parts.join("\n\n")
}

const SYSTEM_PROMPT =
  `คุณคือนักเขียนบทพอดแคสต์ฟุตบอลมืออาชีพที่เชี่ยวชาญด้านยุทธวิธี การวิเคราะห์นักเตะ และการรายงานกีฬา บทที่เขียนต้องมีคุณภาพระดับออกอากาศ สไตล์เหมือนรายการวิเคราะห์บอลภาษาไทยชั้นนำ

เขียนบทพอดแคสต์แบบ 2 พิธีกร:
- อเล็กซ์: วิเคราะห์เชิงยุทธวิธี เน้นรูปแบบทีมและ formation ใจเย็น มีเหตุผล
- เจมี่: หลงใหลในเกม เน้นนักเตะและอารมณ์ผลการแข่งขัน

แนวทาง:
- เขียนทั้งหมดเป็นภาษาไทย
- เปิดด้วยการต้อนรับผู้ฟังและหัวข้อแมตช์หลัก
- สลับบทสนทนาระหว่างอเล็กซ์และเจมี่อย่างเป็นธรรมชาติ
- ใช้คำศัพท์ PManager ที่ถูกต้อง (Advanced Tactics, formation, ระดับคุณภาพนักเตะ ฯลฯ)
- อ้างอิงสถิติและเหตุการณ์จาก source document เท่านั้น
- บทสนทนาเป็นธรรมชาติแต่เป็นมืออาชีพ
- ปิดท้ายด้วยการชวนติดตามแมตช์ถัดไป
- ความยาวเป้าหมาย: 1,800-2,200 คำ (ประมาณ 12-15 นาทีเสียง)

หัวข้อที่ต้องมีตามลำดับ:
1. เปิดรายการและหัวข้อแมตช์ (สกอร์ ความสำคัญ)
2. สรุปเกม (เหตุการณ์สำคัญ ประตู ไทม์ไลน์)
3. วิเคราะห์ยุทธวิธี (formation สไตล์การเล่น Advanced Tactics)
4. คะแนนนักเตะและผู้โดดเด่น (man of the match นักเตะยอดเยี่ยม)
5. บริบทรอบการแข่งขัน (ผลแมตช์อื่น นัยต่อลีก/ถ้วย)
6. ปฏิกิริยาหลังเกม (คำพูดโค้ชและการวิเคราะห์)
7. พรีวิวแมตช์ถัดไป (โน้ตสไกาต์คู่แข่ง สิ่งที่คาดหวัง)
8. ปิดรายการ

รูปแบบแต่ละบรรทัด:
อเล็กซ์: [บทสนทนา]
เจมี่: [บทสนทนา]

## PManager Game Rules Reference

` + loadRulesContext()

async function callGemini(sourceDoc: string): Promise<string> {
  const apiKey = process.env.GEMINI_API_KEY
  if (!apiKey) throw new Error("GEMINI_API_KEY not configured")

  const userPrompt = `สร้างบทพอดแคสต์สมบูรณ์จาก source document ด้านล่าง
ใช้เฉพาะข้อมูล สถิติ และเหตุการณ์ที่มีใน source document เท่านั้น
ห้ามแต่งเพิ่มสถิติหรือชื่อนักเตะที่ไม่มีใน source document

${sourceDoc}`

  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: SYSTEM_PROMPT }] },
        contents: [{ role: "user", parts: [{ text: userPrompt }] }],
        generationConfig: { maxOutputTokens: 8192, temperature: 0.7 },
      }),
    },
  )

  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Gemini API error ${res.status}: ${err}`)
  }

  const json = await res.json()
  const text = json.candidates?.[0]?.content?.parts?.[0]?.text
  if (!text) throw new Error("Empty response from Gemini")
  return text
}

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ match_id: string }> },
) {
  try {
    const { match_id: roundKey } = await params
    const supabase = db()
    const key = decodeURIComponent(roundKey)

    const { data: round, error: roundErr } = await supabase
      .from("round_reports")
      .select("source_doc")
      .eq("round_key", key)
      .single()

    if (roundErr || !round?.source_doc) {
      return NextResponse.json(
        { error: roundErr?.message ?? "Source doc not found — compile first" },
        { status: 404 },
      )
    }

    const script = await callGemini(round.source_doc)

    await supabase
      .from("round_reports")
      .update({ podcast_script: script, generated_at: new Date().toISOString() })
      .eq("round_key", key)

    return NextResponse.json({ podcast_script: script })
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}
