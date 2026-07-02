"""
DifficultyService — AI-powered difficulty prediction.

Input factors: solve_count, wrong_attempts, avg_solve_time_seconds, hint_usage.
Output: Easy | Medium | Hard | Insane + confidence score + explanation.
"""
from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)

_DIFFICULTY_PROMPT = """You are a CTF difficulty analyst. Analyse these statistics for a challenge and predict its difficulty.

Challenge: {title}
Category: {category}
Current difficulty label: {current_difficulty}
Solve count: {solve_count}
Wrong attempts: {wrong_attempts}
Average solve time (seconds): {avg_time:.0f}
Hint usage count: {hint_usage}
Total participants (approx): {total_participants}

Respond ONLY with valid JSON matching exactly this schema (no markdown, no extra text):
{{"predicted_difficulty": "Easy|Medium|Hard|Insane", "confidence": 0.0-1.0, "explanation": "1-2 sentence reason"}}
"""

_LABEL_FALLBACK = {
    'easy': 'Easy', 'medium': 'Medium', 'hard': 'Hard', 'insane': 'Insane',
}


def _parse_difficulty_response(text: str) -> tuple[str, float, str]:
    """Parse model JSON output, with fallback heuristics."""
    # Try direct JSON parse
    try:
        text = text.strip()
        # Sometimes models wrap in ```json ... ```
        text = re.sub(r'^```json\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```$', '', text).strip()
        data = json.loads(text)
        label = _LABEL_FALLBACK.get(data.get('predicted_difficulty', '').lower(), 'Medium')
        conf = float(data.get('confidence', 0.5))
        expl = data.get('explanation', '')
        return label, conf, expl
    except Exception:
        pass

    # Keyword fallback
    lower = text.lower()
    for kw in ('insane', 'hard', 'medium', 'easy'):
        if kw in lower:
            return _LABEL_FALLBACK[kw], 0.5, text[:200]
    return 'Medium', 0.4, text[:200]


class DifficultyService:

    @staticmethod
    def _get_avg_solve_time(challenge) -> float:
        """Average solve time in seconds from Submission records."""
        try:
            from app.models.submission import Submission
            from app.extensions import db
            solves = Submission.query.filter_by(
                challenge_id=challenge.id, correct=True
            ).all()
            if not solves:
                return 0.0
            times = []
            for s in solves:
                if hasattr(s, 'elapsed_seconds') and s.elapsed_seconds:
                    times.append(float(s.elapsed_seconds))
            return sum(times) / len(times) if times else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _get_hint_usage(challenge) -> int:
        try:
            from app.models.hint import HintUnlock
            from app.extensions import db
            hint_ids = [h.id for h in challenge.hints]
            if not hint_ids:
                return 0
            return HintUnlock.query.filter(HintUnlock.hint_id.in_(hint_ids)).count()
        except Exception:
            return 0

    @staticmethod
    def _get_total_participants() -> int:
        try:
            from app.models.user import User
            return User.query.filter_by(is_deleted=False).count()
        except Exception:
            return 1

    @staticmethod
    def predict(challenge) -> dict:
        """
        Run AI difficulty prediction for a challenge.

        Returns dict with: predicted_difficulty, confidence, explanation,
                           tokens_used, provider, record_id.
        """
        from app.services.ai_service import AIService
        from app.models.ai_difficulty_prediction import AIDifficultyPrediction
        from app.extensions import db

        avg_time = DifficultyService._get_avg_solve_time(challenge)
        hint_usage = DifficultyService._get_hint_usage(challenge)
        total = DifficultyService._get_total_participants()

        try:
            cat_name = challenge.category.name if challenge.category else 'Unknown'
        except Exception:
            cat_name = 'Unknown'

        prompt = _DIFFICULTY_PROMPT.format(
            title=challenge.title,
            category=cat_name,
            current_difficulty=challenge.difficulty or 'Unknown',
            solve_count=challenge.solve_count,
            wrong_attempts=challenge.attempt_count - challenge.solve_count,
            avg_time=avg_time,
            hint_usage=hint_usage,
            total_participants=total,
        )

        try:
            response, tokens, provider = AIService.generate(prompt, max_tokens=200)
        except ValueError as exc:
            logger.warning('[DifficultyService] Security violation: %s', exc)
            return {'error': str(exc)}

        label, conf, explanation = _parse_difficulty_response(response)

        record = AIDifficultyPrediction(
            challenge_id=challenge.id,
            solve_count=challenge.solve_count,
            wrong_attempts=max(0, challenge.attempt_count - challenge.solve_count),
            avg_solve_time_seconds=avg_time,
            hint_usage_count=hint_usage,
            prompt=prompt,
            response=response,
            tokens_used=tokens,
            predicted_difficulty=label,
            confidence_score=conf,
            explanation=explanation,
            provider=provider,
        )
        db.session.add(record)
        db.session.commit()

        return {
            'predicted_difficulty': label,
            'confidence': conf,
            'explanation': explanation,
            'tokens_used': tokens,
            'provider': provider,
            'record_id': record.id,
        }

    @staticmethod
    def get_latest_prediction(challenge_id: int) -> dict | None:
        try:
            from app.models.ai_difficulty_prediction import AIDifficultyPrediction
            rec = (
                AIDifficultyPrediction.query
                .filter_by(challenge_id=challenge_id)
                .order_by(AIDifficultyPrediction.id.desc())
                .first()
            )
            if not rec:
                return None
            return {
                'predicted_difficulty': rec.predicted_difficulty,
                'confidence': rec.confidence_score,
                'explanation': rec.explanation,
                'created_at': rec.created_at.isoformat(),
            }
        except Exception:
            return None
