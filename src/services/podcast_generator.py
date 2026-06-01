"""
Podcast script generator using the Google Gemini API.

Takes the compiled source document (Markdown) and returns a dual-host
podcast script in the style of Sky Sports / BBC Sport football coverage.
The script is ready for manual upload to NotebookLM for Audio Overview
generation.
"""

from __future__ import annotations

from google import genai
from google.genai import types

from src.config import config
from src.core.logger import logger

_SYSTEM_PROMPT = """\
You are a professional football podcast scriptwriter with expertise in football tactics,
player analysis, and sports broadcasting. Your scripts are broadcast-quality and match
the tone of Sky Sports and BBC Sport football coverage.

Write dual-host podcast scripts. The two hosts are:
- Alex: analytical, focused on tactics and formations, measured in tone
- Jamie: passionate, player-focused, emotionally engaged with results

Guidelines:
- Open with a brief welcome and match headline
- Alternate dialogue naturally between Alex and Jamie
- Include all required segments in order (see below)
- Use PManager-specific terminology accurately (Advanced Tactics, formations, quality tiers, etc.)
- Reference specific match statistics and events from the source document
- Keep banter natural but professional — this is a sports analysis show
- Close with a brief sign-off teasing next fixture
- Target length: 1,800-2,200 words (approximately 12-15 minutes of audio)

Required segments in this order:
1. Intro and Match Headline (score, significance)
2. Match Recap (key events, goals, timeline)
3. Tactical Breakdown (formations, styles, Advanced Tactics used vs expected)
4. Player Ratings and Standouts (man of match, top performers)
5. Matchday Context (other results, league/cup implications)
6. Post-Match Reaction (manager quotes and analysis)
7. Next Fixture Preview (opponent scout notes, what to expect)
8. Sign-off

Format each line as:
Alex: [dialogue]
Jamie: [dialogue]
"""

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
