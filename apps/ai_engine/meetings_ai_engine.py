"""LLM logic for meeting chunk analysis."""

from __future__ import annotations

import json
import os
from typing import Any

import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"
REQUEST_TIMEOUT_SECONDS = 30


def call_llm(prompt: str) -> str:
    """Send a prompt to Groq and return the raw text response."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return ""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You analyze meeting transcripts and follow output instructions "
                    "exactly."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return ""


def _parse_summary_lines(raw_text: str) -> list[str]:
    """Convert a bullet-style LLM response into a clean summary list."""
    summary_points: list[str] = []

    for line in raw_text.splitlines():
        cleaned_line = line.strip()
        if not cleaned_line:
            continue

        cleaned_line = cleaned_line.lstrip("-* ").strip()
        if not cleaned_line:
            continue

        summary_points.append(cleaned_line)

    return summary_points


def _extract_json_block(raw_text: str) -> str:
    """Extract a JSON array from a raw LLM response."""
    stripped_text = raw_text.strip()

    if stripped_text.startswith("```"):
        lines = stripped_text.splitlines()
        if len(lines) >= 3:
            stripped_text = "\n".join(lines[1:-1]).strip()

    start_index = stripped_text.find("[")
    end_index = stripped_text.rfind("]")
    if start_index == -1 or end_index == -1 or end_index < start_index:
        return ""

    return stripped_text[start_index : end_index + 1]


def generate_summary(chunk_text: str) -> list[str]:
    """Generate 5-10 concise summary points for a meeting chunk."""
    prompt = f"""
Analyze the following meeting transcript chunk.

Return 5 to 10 concise bullet points.
Focus only on:
- decisions made
- important discussion points
- commitments that affect the meeting outcome

Ignore filler conversation, greetings, and small talk.

Transcript:
{chunk_text}
""".strip()

    raw_response = call_llm(prompt)
    if not raw_response:
        return []

    return _parse_summary_lines(raw_response)


def extract_tasks(chunk_text: str) -> list[dict[str, Any]]:
    """Extract only actionable follow-up tasks as strict JSON."""
    prompt = f"""
Extract ONLY actionable tasks from the meeting transcript below.

A valid task must:
- include a clear action
- imply commitment or assignment
- require follow-up

Do NOT include:
- discussion topics
- suggestions without commitment
- vague ideas
- observations

Priority rules:
- High = urgent deadlines or critical tasks
- Medium = normal tasks
- Low = optional or minor tasks

Speaker rules:
- Use speaker IDs exactly as written, such as speaker_5
- Do NOT guess names
- If a name is explicitly stated, you may format as "speaker_X (Name)"

Return STRICT JSON only.
Return a JSON array in this exact shape:
[
  {{
    "task": "Prepare report",
    "owner": "speaker_5",
    "priority": "High"
  }}
]

Transcript:
{chunk_text}
""".strip()

    raw_response = call_llm(prompt)
    if not raw_response:
        return []

    try:
        json_block = _extract_json_block(raw_response)
        parsed_tasks = json.loads(json_block)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []

    if not isinstance(parsed_tasks, list):
        return []

    clean_tasks: list[dict[str, Any]] = []
    for item in parsed_tasks:
        if not isinstance(item, dict):
            continue

        task_text = str(item.get("task", "")).strip()
        owner = str(item.get("owner", "")).strip()
        priority = str(item.get("priority", "Medium")).strip().title()

        if not task_text or not owner:
            continue

        if priority not in {"High", "Medium", "Low"}:
            priority = "Medium"

        clean_tasks.append(
            {
                "task": task_text,
                "owner": owner,
                "priority": priority,
            }
        )

    return clean_tasks


def analyze_chunk(chunk_text: str) -> dict[str, list[Any]]:
    """Generate summary points and action items for one transcript chunk."""
    summary = generate_summary(chunk_text)
    tasks = extract_tasks(chunk_text)
    return {
        "summary": summary,
        "tasks": tasks,
    }


def process_meeting_text(text: str) -> dict[str, list[Any]]:
    """Backward-compatible wrapper for existing callers."""
    return analyze_chunk(text)
