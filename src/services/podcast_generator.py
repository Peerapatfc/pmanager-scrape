"""
Podcast script generator using the Google Gemini API.

Takes the compiled source document (Markdown) and returns a dual-host
podcast script in the style of Sky Sports / BBC Sport football coverage.
The script is ready for manual upload to NotebookLM for Audio Overview
generation.
"""

from __future__ import annotations

from pathlib import Path

from google import genai
from google.genai import types

from src.config import config
from src.core.logger import logger

_MANUAL_DIR = Path(__file__).parent.parent.parent / "docs" / "manual" / "sections"
_MANUAL_SECTIONS = ["section_13.md", "section_14.md", "section_34.md", "section_20.md"]
_MAX_SECTION_CHARS = 3000


def _load_rules_context() -> str:
    parts = []
    for fname in _MANUAL_SECTIONS:
        path = _MANUAL_DIR / fname
        try:
            content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        if len(content) > _MAX_SECTION_CHARS:
            content = content[:_MAX_SECTION_CHARS].rsplit("\n", 1)[0]
        parts.append(content)
    return "\n\n".join(parts)


_SYSTEM_PROMPT = """\
คุณคือนักเขียนบทพอดแคสต์ฟุตบอลมืออาชีพที่เชี่ยวชาญด้านยุทธวิธี การวิเคราะห์นักเตะ และการรายงานกีฬา \
บทที่เขียนต้องมีคุณภาพระดับออกอากาศ สไตล์เหมือนรายการวิเคราะห์บอลภาษาไทยชั้นนำ

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
"""

_SYSTEM_PROMPT += "\n\n## PManager Game Rules Reference\n\n" + _load_rules_context()

_USER_PROMPT_TEMPLATE = """\
Generate a complete podcast script for the match described below.
Use ONLY the facts, statistics, and context provided in the source document.
Do not invent statistics or player names not mentioned in the source.

{source_doc}
"""

_MODEL = "gemini-2.5-flash"


class PodcastGenerator:
    """Generates dual-host podcast scripts via the Google Gemini API."""

    def __init__(self) -> None:
        self._client = genai.Client(api_key=config.GEMINI_API_KEY)

    def generate(self, source_doc: str) -> str:
        """Generate a podcast script from the source document.

        Args:
            source_doc: Compiled Markdown source document from PodcastCompiler.

        Returns:
            Full podcast script as a string.
        """
        logger.info("Generating podcast script via Gemini API (%s)...", _MODEL)
        prompt = _USER_PROMPT_TEMPLATE.format(source_doc=source_doc)

        response = self._client.models.generate_content(
            model=_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                max_output_tokens=8192,
                temperature=0.7,
            ),
        )

        script = response.text
        logger.info(
            "Podcast script generated: %d words, %d chars",
            len(script.split()),
            len(script),
        )
        return script
