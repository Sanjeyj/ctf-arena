"""
WriteupService — AI-generated educational writeups with draft→approved→published workflow.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_WRITEUP_PROMPT = """You are an expert CTF player writing an educational post-competition writeup.

Challenge: {title}
Category: {category}
Description: {description}
Points: {points}

Write a structured educational writeup with these three sections:
1. Summary (2-3 sentences overview of what the challenge was about)
2. Steps (numbered step-by-step solution approach — do NOT include the actual flag value)
3. Learning Points (2-3 key takeaways for students)

Format your response EXACTLY as:
SUMMARY: <text>
STEPS: <numbered list>
LEARNING POINTS: <bulleted list>
"""


def _parse_writeup(text: str) -> tuple[str, str, str]:
    """Extract Summary, Steps, Learning Points from structured model output."""
    import re
    summary, steps, learning = '', '', ''

    summary_m = re.search(r'SUMMARY:\s*(.*?)(?=STEPS:|$)', text, re.IGNORECASE | re.DOTALL)
    steps_m = re.search(r'STEPS:\s*(.*?)(?=LEARNING POINTS:|$)', text, re.IGNORECASE | re.DOTALL)
    learning_m = re.search(r'LEARNING POINTS:\s*(.*?)$', text, re.IGNORECASE | re.DOTALL)

    if summary_m:
        summary = summary_m.group(1).strip()
    if steps_m:
        steps = steps_m.group(1).strip()
    if learning_m:
        learning = learning_m.group(1).strip()

    # Fallback: dump everything into summary
    if not summary:
        summary = text.strip()

    return summary, steps, learning


class WriteupService:

    @staticmethod
    def generate(challenge, requesting_user=None) -> dict:
        """
        Generate an AI writeup for a challenge.
        Returns dict with: writeup_id, status, summary, steps, learning_points, tokens_used.
        """
        from app.services.ai_service import AIService
        from app.models.ai_writeup import AIWriteup
        from app.extensions import db

        try:
            cat_name = challenge.category.name if challenge.category else 'Unknown'
        except Exception:
            cat_name = 'Unknown'

        prompt = _WRITEUP_PROMPT.format(
            title=challenge.title,
            category=cat_name,
            description=(challenge.description or '')[:500],
            points=challenge.points,
        )

        try:
            response, tokens, provider = AIService.generate(prompt, max_tokens=600)
        except ValueError as exc:
            logger.warning('[WriteupService] Security violation: %s', exc)
            return {'error': str(exc)}

        summary, steps, learning = _parse_writeup(response)

        record = AIWriteup(
            user_id=requesting_user.id if requesting_user else None,
            challenge_id=challenge.id,
            prompt=prompt,
            response=response,
            tokens_used=tokens,
            provider=provider,
            summary=summary,
            steps=steps,
            learning_points=learning,
            status='draft',
            approved=False,
            published=False,
        )
        db.session.add(record)
        db.session.commit()

        return {
            'writeup_id': record.id,
            'status': 'draft',
            'summary': summary,
            'steps': steps,
            'learning_points': learning,
            'tokens_used': tokens,
            'provider': provider,
        }

    @staticmethod
    def approve(writeup_id: int) -> dict:
        """Admin approves a draft writeup."""
        from app.models.ai_writeup import AIWriteup
        from app.extensions import db
        rec = AIWriteup.query.get(writeup_id)
        if not rec:
            return {'error': 'Writeup not found.'}
        rec.approved = True
        rec.status = 'approved'
        db.session.commit()
        return {'writeup_id': writeup_id, 'status': 'approved'}

    @staticmethod
    def publish(writeup_id: int) -> dict:
        """Admin publishes an approved writeup."""
        from app.models.ai_writeup import AIWriteup
        from app.extensions import db
        rec = AIWriteup.query.get(writeup_id)
        if not rec:
            return {'error': 'Writeup not found.'}
        if not rec.approved:
            return {'error': 'Writeup must be approved before publishing.'}
        rec.published = True
        rec.status = 'published'
        db.session.commit()
        return {'writeup_id': writeup_id, 'status': 'published'}

    @staticmethod
    def get_published(challenge_id: int) -> dict | None:
        """Fetch the latest published writeup for a challenge."""
        try:
            from app.models.ai_writeup import AIWriteup
            rec = (
                AIWriteup.query
                .filter_by(challenge_id=challenge_id, published=True)
                .order_by(AIWriteup.id.desc())
                .first()
            )
            if not rec:
                return None
            return {
                'id': rec.id,
                'summary': rec.summary,
                'steps': rec.steps,
                'learning_points': rec.learning_points,
                'created_at': rec.created_at.isoformat(),
            }
        except Exception:
            return None

    @staticmethod
    def list_all(status: str | None = None) -> list[dict]:
        """List writeups optionally filtered by status."""
        try:
            from app.models.ai_writeup import AIWriteup
            q = AIWriteup.query
            if status:
                q = q.filter_by(status=status)
            records = q.order_by(AIWriteup.id.desc()).all()
            return [
                {
                    'id': r.id,
                    'challenge_id': r.challenge_id,
                    'status': r.status,
                    'tokens_used': r.tokens_used,
                    'created_at': r.created_at.isoformat(),
                }
                for r in records
            ]
        except Exception:
            return []
