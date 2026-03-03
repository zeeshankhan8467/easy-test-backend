"""
AI Question Generator Service using Groq API (OpenAI-compatible)
Uses Llama models via https://api.groq.com/openai/v1
"""
import json
import logging
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Groq uses OpenAI-compatible API
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Default: fast model; use llama-3.3-70b-versatile for higher quality
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.1-8b-instant"
HIGH_QUALITY_MODEL = "llama-3.3-70b-versatile"


class GroqQuestionGenerator:
    """Generate MCQ and other question types using Groq (Llama) API."""

    def __init__(self) -> None:
        if not OPENAI_AVAILABLE:
            raise ValueError(
                "openai package is required for Groq. Run: pip install openai"
            )
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is not set. "
                "Get a key from: https://console.groq.com/keys"
            )
        model = os.getenv("GROQ_MODEL", DEFAULT_MODEL).strip()
        if model not in (DEFAULT_MODEL, HIGH_QUALITY_MODEL):
            model = DEFAULT_MODEL
        self.model = model
        self.client = OpenAI(
            api_key=api_key,
            base_url=GROQ_BASE_URL,
        )

    def _build_prompt(self, topic: str, count: int, difficulty: str, qtype: str, num_options: int = 4) -> str:
        """Build an exam-level prompt for AI question generation."""
        difficulty_description = {
            "easy": "basic, recall-level concepts suitable for beginners",
            "medium": "intermediate concepts requiring application and understanding",
            "hard": "advanced concepts requiring analysis, evaluation, or synthesis",
        }
        diff_desc = difficulty_description.get(
            difficulty, difficulty_description["medium"]
        )

        n_opts = max(2, min(15, num_options)) if qtype == "mcq" else 4
        mcq_instruction = f"""Generate Multiple Choice Questions (MCQ) with exactly {n_opts} options each.
- "question": Question text in HTML (use <p>, <strong>, <em>, <u> only). One clear stem, exam-style.
- "options": Array of exactly {n_opts} options. One clearly correct; others plausible distractors.
- "correct_answer": Index of correct option (0 to {n_opts - 1}).
- "marks": Number (e.g. 0.5, 1.0, 1.5, 2.0).
- "explanation": Brief, factual explanation of the correct answer.

Example (4 options):
{{"question": "<p>What is the <strong>primary purpose</strong> of an <em>if</em> statement?</p>", "options": ["Define a function", "Make decisions based on conditions", "Loop through data", "Import modules"], "correct_answer": 1, "marks": 1.0, "explanation": "The if statement is used for conditional execution."}}
You MUST use exactly {n_opts} options in the "options" array for each question."""

        question_type_instructions = {
            "mcq": mcq_instruction,
            "true_false": """Generate True/False questions.
- "question": Statement in HTML. Must be unambiguously true or false.
- "options": ["True", "False"]
- "correct_answer": 0 for True, 1 for False
- "marks": Number
- "explanation": Brief explanation

Example:
{"question": "<p>Python is a <strong>compiled</strong> language.</p>", "options": ["True", "False"], "correct_answer": 1, "marks": 1.0, "explanation": "Python is interpreted, not compiled."}""",
            "multiple_select": """Generate Multiple Select questions (more than one correct).
- "question": Question in HTML. Clearly state that more than one may be correct.
- "options": Array of 4-5 options
- "correct_answer": Array of indices, e.g. [0, 2]
- "marks": Number
- "explanation": Brief explanation

Example:
{"question": "<p>Which are <strong>Python</strong> data types?</p>", "options": ["list", "dictionary", "array", "tuple", "set"], "correct_answer": [0, 1, 3, 4], "marks": 2.0, "explanation": "list, dict, tuple, set are built-in; array is from numpy."}""",
        }
        type_instructions = question_type_instructions.get(
            qtype, question_type_instructions["mcq"]
        )

        return f"""You are an expert exam writer. Generate exactly {count} {difficulty}-level {qtype} questions on the topic: "{topic}".

Difficulty: {diff_desc}

{type_instructions}

Rules:
- Exam-quality: clear stem, no ambiguity, one best answer for MCQ.
- Topic: every question must clearly relate to "{topic}".
- HTML only: <p>, <strong>, <em>, <u>. Wrap each question in <p>.
- Marks: use numbers (0.5, 1.0, 1.5, 2.0) by difficulty.
- For MCQ: correct_answer is a single integer 0 to (number of options minus 1). For True/False: 0 or 1. For multiple_select: array of indices e.g. [0, 2].

Output ONLY a valid JSON array of {count} question objects. No markdown, no code fences, no extra text.
[
  {{"question": "...", "options": [...], "correct_answer": ..., "marks": ..., "explanation": "..."}},
  ...
]"""

    def _parse_json_response(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse AI response into a list of question dicts.
        Handles markdown fences and invalid JSON with clear errors.
        """
        raw = content.strip()
        # Strip markdown code blocks
        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        # Try direct parse
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            # Try to extract a JSON array
            match = re.search(r"\[[\s\S]*\]", raw)
            if match:
                try:
                    parsed = json.loads(match.group())
                except json.JSONDecodeError as e2:
                    logger.warning("Invalid JSON in AI response (extracted): %s", e2)
                    raise ValueError(
                        f"AI returned invalid JSON. Parse error: {e2}. "
                        f"First 300 chars: {raw[:300]}"
                    ) from e2
            else:
                logger.warning("No JSON array in AI response: %s", raw[:200])
                raise ValueError(
                    f"AI response is not valid JSON. Parse error: {e}. "
                    f"First 300 chars: {raw[:300]}"
                ) from e

        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            if "questions" in parsed:
                return parsed["questions"]
            if "question" in parsed:
                return [parsed]
            return [parsed]
        raise ValueError(
            f"AI response was not a JSON array or object. Got: {type(parsed).__name__}"
        )

    def generate_questions(
        self, topic: str, count: int, difficulty: str, qtype: str, num_options: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Generate questions using Groq API.

        Args:
            topic: Subject/topic for questions
            count: Number of questions (1-20)
            difficulty: easy, medium, or hard
            qtype: mcq, true_false, or multiple_select
            num_options: For MCQ, number of options per question (2-15, default 4)

        Returns:
            List of dicts with: text, options, correct_answer, explanation, difficulty, tags, marks
        """
        prompt = self._build_prompt(topic, count, difficulty, qtype, num_options)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an exam question generator. Reply only with a valid JSON array of question objects. No markdown, no explanation outside the array.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=max(2048, 500 * count),
        )

        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise ValueError("Groq API returned empty response.")

        questions = self._parse_json_response(content)

        # Normalize and validate
        formatted: List[Dict[str, Any]] = []
        for q in questions[:count]:
            if not isinstance(q, dict):
                continue
            question_text = (q.get("question") or "").strip()
            options = q.get("options")
            if not question_text or not isinstance(options, list) or not options:
                continue

            correct_answer = q.get("correct_answer")
            if qtype == "multiple_select":
                if not isinstance(correct_answer, list):
                    correct_answer = (
                        [correct_answer] if correct_answer is not None else []
                    )
            else:
                if isinstance(correct_answer, list):
                    correct_answer = correct_answer[0] if correct_answer else 0
                correct_answer = int(correct_answer) if correct_answer is not None else 0

            marks = q.get("marks", 1.0)
            if isinstance(marks, str):
                try:
                    marks = float(marks)
                except (TypeError, ValueError):
                    marks = 1.0
            elif not isinstance(marks, (int, float)):
                marks = 1.0
            if marks == 1.0:
                marks = {"easy": 0.5, "medium": 1.0, "hard": 1.5}.get(
                    difficulty, 1.0
                )

            formatted.append({
                "text": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": (q.get("explanation") or "").strip(),
                "difficulty": difficulty,
                "tags": [topic],
                "marks": float(marks),
            })

        return formatted

    def generate_questions_safe(
        self, topic: str, count: int, difficulty: str, qtype: str, num_options: int = 4
    ) -> List[Dict[str, Any]]:
        """Safe wrapper: returns empty list on any failure."""
        try:
            return self.generate_questions(topic, count, difficulty, qtype, num_options)
        except Exception as e:
            logger.exception("Groq AI generation error: %s", e)
            return []
