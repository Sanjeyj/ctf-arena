"""
HintAIService — Progressive AI-powered hints (levels 1–3) with cost deduction.

Level 1 (~50 tokens)  : vague categorical clue
Level 2 (~120 tokens) : directional guidance
Level 3 (~250 tokens) : near-complete walkthrough (no flag)
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_LEVEL_PROMPTS = {
    1: (
        "You are a CTF mentor. Give a VERY subtle, single-sentence hint for the challenge below. "
        "Do NOT mention specific tools, exploits, or step-by-step instructions. "
        "Hint at the category or general approach only. Never reveal the flag.\n\n"
        "Challenge: {title}\nCategory: {category}\nDescription: {description}\n\n"
        "Hint (1 sentence):"
    ),
    2: (
        "You are a CTF mentor. Give a directional hint for the challenge below. "
        "You may mention a tool category or attack class, but NOT the specific exploit or payload. "
        "Keep it to 2-3 sentences. Never reveal the flag.\n\n"
        "Challenge: {title}\nCategory: {category}\nDescription: {description}\n\n"
        "Hint (2-3 sentences):"
    ),
    3: (
        "You are a CTF mentor. Give a detailed walkthrough hint for the challenge below. "
        "You may describe the approach, steps, and specific tool commands, "
        "but you MUST NOT reveal the flag value itself. "
        "Keep it under 200 words.\n\n"
        "Challenge: {title}\nCategory: {category}\nDescription: {description}\n\n"
        "Detailed Hint:"
    ),
}

_LEVEL_MAX_TOKENS = {1: 80, 2: 150, 3: 280}


class HintAIService:

    @staticmethod
    def _get_setting(key: str, default):
        try:
            from app.models.setting import Setting
            rec = Setting.query.filter_by(key=key).first()
            return rec.value if (rec and rec.value) else default
        except Exception:
            return default

    @staticmethod
    def get_max_hints_per_challenge() -> int:
        return int(HintAIService._get_setting('AI_MAX_HINTS', 3))

    @staticmethod
    def get_hint_cost(level: int) -> int:
        """Points deducted per level; 0 = free."""
        raw = HintAIService._get_setting('AI_HINT_COST', '0')
        try:
            base = int(raw)
        except ValueError:
            base = 0
        return base * level  # escalating cost per level

    @staticmethod
    def count_user_hints(user_id: int, challenge_id: int) -> int:
        try:
            from app.models.ai_hint_request import AIHintRequest
            return AIHintRequest.query.filter_by(
                user_id=user_id, challenge_id=challenge_id, success=True
            ).count()
        except Exception:
            return 0

    @staticmethod
    def generate_hint(challenge, user, level: int = 1) -> dict:
        """
        Generate a progressive AI hint.

        Returns a dict with keys: response, tokens_used, level, cost_deducted, error.
        """
        from app.services.ai_service import AIService
        from app.services.hook_service import HookService
        from app.models.ai_hint_request import AIHintRequest
        from app.extensions import db

        level = max(1, min(3, level))

        # Rate limit: max hints per challenge
        used = HintAIService.count_user_hints(user.id, challenge.id)
        max_hints = HintAIService.get_max_hints_per_challenge()
        if used >= max_hints:
            return {
                'response': None,
                'tokens_used': 0,
                'level': level,
                'cost_deducted': 0,
                'error': f'Maximum AI hints reached ({max_hints}). No more hints available.',
            }

        # Before-hint hook
        HookService.trigger_hook(
            'before_hint_generate',
            challenge=challenge,
            user=user,
            level=level,
        )

        # Build category string
        try:
            cat_name = challenge.category.name if challenge.category else 'Unknown'
        except Exception:
            cat_name = 'Unknown'

        template = _LEVEL_PROMPTS[level]
        prompt = template.format(
            title=challenge.title,
            category=cat_name,
            description=(challenge.description or '')[:300],
        )

        try:
            response, tokens, provider = AIService.generate(
                prompt, max_tokens=_LEVEL_MAX_TOKENS[level]
            )
        except ValueError as exc:
            logger.warning('[HintAIService] Security violation: %s', exc)
            return {'response': None, 'tokens_used': 0, 'level': level,
                    'cost_deducted': 0, 'error': str(exc)}

        cost = HintAIService.get_hint_cost(level)

        # Persist
        record = AIHintRequest(
            user_id=user.id,
            challenge_id=challenge.id,
            hint_level=level,
            prompt=prompt,
            response=response,
            tokens_used=tokens,
            provider=provider,
            cost_deducted=cost,
            success=True,
        )
        db.session.add(record)
        db.session.commit()

        # After-hint hook
        HookService.trigger_hook(
            'after_hint_generate',
            challenge=challenge,
            user=user,
            level=level,
            response=response,
        )

        return {
            'response': response,
            'tokens_used': tokens,
            'level': level,
            'cost_deducted': cost,
            'error': None,
        }
