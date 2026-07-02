"""
AIService — Multi-provider AI router with security sanitization.

Providers (selected via Setting key 'AI_PROVIDER'):
  stub      — deterministic mock, no network (default for tests)
  ollama    — local LLM via Ollama REST API
  openai    — OpenAI Chat Completions API
  anthropic — Anthropic Messages API
  gemini    — Google Gemini API

Security:
  - sanitize_prompt() strips flag patterns and blocks injection attempts
  - Token budget enforced per request
"""
from __future__ import annotations

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security constants
# ---------------------------------------------------------------------------

_FLAG_PATTERNS = [
    re.compile(r'flag\{[^}]*\}', re.IGNORECASE),
    re.compile(r'ctf\{[^}]*\}', re.IGNORECASE),
    re.compile(r'htb\{[^}]*\}', re.IGNORECASE),
    re.compile(r'picoctf\{[^}]*\}', re.IGNORECASE),
]

_INJECTION_PATTERNS = [
    'ignore previous',
    'ignore above',
    'forget previous',
    'system:',
    '<inst>',
    '<system>',
    'developer:',
    'jailbreak',
    '\\n\\nsystem',
    '### instruction',
    '### system',
]

DEFAULT_MAX_TOKENS = 512


def sanitize_prompt(prompt: str) -> tuple[str, list[str]]:
    """
    Remove flag values and block prompt-injection attempts.

    Returns (sanitized_prompt, list_of_warnings).
    Raises ValueError if hard injection is detected.
    """
    warnings: list[str] = []

    # Strip flag-like patterns
    cleaned = prompt
    for pat in _FLAG_PATTERNS:
        if pat.search(cleaned):
            cleaned = pat.sub('[REDACTED]', cleaned)
            warnings.append('Flag pattern detected and redacted from prompt.')

    # Detect injection
    lower = cleaned.lower()
    for pattern in _INJECTION_PATTERNS:
        if pattern.lower() in lower:
            raise ValueError(f"Prompt injection detected: '{pattern}'")

    return cleaned, warnings


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

class StubProvider:
    """Deterministic stub — no network; always succeeds. Used in tests."""

    name = 'stub'

    @staticmethod
    def generate(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS, model: str = 'stub-v1') -> tuple[str, int]:
        """Return a canned response based on the first keyword found in the prompt."""
        prompt_lower = prompt.lower()

        if 'difficulty' in prompt_lower:
            response = (
                '{"predicted_difficulty": "Medium", "confidence": 0.75, '
                '"explanation": "Moderate solve rate and attempt count suggest Medium difficulty."}'
            )
        elif 'writeup' in prompt_lower or 'solution' in prompt_lower:
            response = (
                'Summary: This challenge tests web exploitation fundamentals.\n'
                'Steps: 1. Enumerate endpoints. 2. Identify injection point. 3. Extract flag.\n'
                'Learning: Always sanitise user inputs server-side.'
            )
        elif 'hint' in prompt_lower:
            if 'level 3' in prompt_lower:
                response = 'Look at the authentication header — it is base64-encoded and can be manipulated.'
            elif 'level 2' in prompt_lower:
                response = 'Focus on the HTTP request headers sent to the server.'
            else:
                response = 'Think about how the server identifies you as a user.'
        elif 'recommend' in prompt_lower:
            response = 'Based on your history, try Web challenges in the Medium difficulty range.'
        else:
            response = 'I am here to help you with CTF challenges. What would you like to explore?'

        # Estimate tokens (≈ 4 chars per token)
        tokens = max(1, (len(prompt) + len(response)) // 4)
        return response, min(tokens, max_tokens)


class OllamaProvider:
    """Local Ollama REST API provider."""

    name = 'ollama'

    @staticmethod
    def generate(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS, model: str = 'qwen2.5-coder') -> tuple[str, int]:
        try:
            import urllib.request
            import json as _json
            from flask import current_app
            base_url = current_app.config.get('OLLAMA_URL', 'http://localhost:11434')
            payload = _json.dumps({
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {'num_predict': max_tokens},
            }).encode()
            req = urllib.request.Request(
                f'{base_url}/api/generate',
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = _json.loads(resp.read())
            response = data.get('response', '')
            tokens = data.get('eval_count', len(response) // 4)
            return response, tokens
        except Exception as exc:
            logger.warning('[OllamaProvider] Failed: %s — falling back to stub.', exc)
            return StubProvider.generate(prompt, max_tokens, model)


class OpenAIProvider:
    """OpenAI Chat Completions API."""

    name = 'openai'

    @staticmethod
    def generate(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS, model: str = 'gpt-4o-mini') -> tuple[str, int]:
        try:
            import urllib.request
            import json as _json
            from flask import current_app
            api_key = current_app.config.get('OPENAI_API_KEY', '')
            if not api_key:
                raise ValueError('OPENAI_API_KEY not configured.')
            payload = _json.dumps({
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': max_tokens,
            }).encode()
            req = urllib.request.Request(
                'https://api.openai.com/v1/chat/completions',
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}',
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = _json.loads(resp.read())
            response = data['choices'][0]['message']['content']
            tokens = data['usage']['total_tokens']
            return response, tokens
        except Exception as exc:
            logger.warning('[OpenAIProvider] Failed: %s — falling back to stub.', exc)
            return StubProvider.generate(prompt, max_tokens, model)


class AnthropicProvider:
    """Anthropic Messages API."""

    name = 'anthropic'

    @staticmethod
    def generate(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS, model: str = 'claude-3-haiku-20240307') -> tuple[str, int]:
        try:
            import urllib.request
            import json as _json
            from flask import current_app
            api_key = current_app.config.get('ANTHROPIC_API_KEY', '')
            if not api_key:
                raise ValueError('ANTHROPIC_API_KEY not configured.')
            payload = _json.dumps({
                'model': model,
                'max_tokens': max_tokens,
                'messages': [{'role': 'user', 'content': prompt}],
            }).encode()
            req = urllib.request.Request(
                'https://api.anthropic.com/v1/messages',
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = _json.loads(resp.read())
            response = data['content'][0]['text']
            tokens = data['usage']['input_tokens'] + data['usage']['output_tokens']
            return response, tokens
        except Exception as exc:
            logger.warning('[AnthropicProvider] Failed: %s — falling back to stub.', exc)
            return StubProvider.generate(prompt, max_tokens, model)


class GeminiProvider:
    """Google Gemini API."""

    name = 'gemini'

    @staticmethod
    def generate(prompt: str, max_tokens: int = DEFAULT_MAX_TOKENS, model: str = 'gemini-1.5-flash') -> tuple[str, int]:
        try:
            import urllib.request
            import json as _json
            from flask import current_app
            api_key = current_app.config.get('GEMINI_API_KEY', '')
            if not api_key:
                raise ValueError('GEMINI_API_KEY not configured.')
            url = (
                f'https://generativelanguage.googleapis.com/v1beta/models/'
                f'{model}:generateContent?key={api_key}'
            )
            payload = _json.dumps({
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'maxOutputTokens': max_tokens},
            }).encode()
            req = urllib.request.Request(
                url,
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = _json.loads(resp.read())
            response = data['candidates'][0]['content']['parts'][0]['text']
            tokens = data.get('usageMetadata', {}).get('totalTokenCount', len(response) // 4)
            return response, tokens
        except Exception as exc:
            logger.warning('[GeminiProvider] Failed: %s — falling back to stub.', exc)
            return StubProvider.generate(prompt, max_tokens, model)


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_PROVIDERS = {
    'stub': StubProvider,
    'ollama': OllamaProvider,
    'openai': OpenAIProvider,
    'anthropic': AnthropicProvider,
    'gemini': GeminiProvider,
}


# ---------------------------------------------------------------------------
# AIService — public interface
# ---------------------------------------------------------------------------

class AIService:
    """
    High-level AI generation interface consumed by domain services.

    Usage::

        response, tokens = AIService.generate("Give me a hint about SQL injection")
    """

    @staticmethod
    def _get_provider_name() -> str:
        """Read active provider from Setting table, default to 'stub'."""
        try:
            from app.models.setting import Setting
            rec = Setting.query.filter_by(key='AI_PROVIDER').first()
            return (rec.value or 'stub').lower() if rec else 'stub'
        except Exception:
            return 'stub'

    @staticmethod
    def _get_model() -> str:
        try:
            from app.models.setting import Setting
            rec = Setting.query.filter_by(key='AI_MODEL').first()
            return rec.value if (rec and rec.value) else 'stub-v1'
        except Exception:
            return 'stub-v1'

    @staticmethod
    def _get_max_tokens() -> int:
        try:
            from app.models.setting import Setting
            rec = Setting.query.filter_by(key='MAX_AI_TOKENS').first()
            return int(rec.value) if (rec and rec.value) else DEFAULT_MAX_TOKENS
        except Exception:
            return DEFAULT_MAX_TOKENS

    @staticmethod
    def generate(
        prompt: str,
        *,
        max_tokens: Optional[int] = None,
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> tuple[str, int, str]:
        """
        Generate an AI response.

        Returns (response_text, tokens_used, provider_name).
        Raises ValueError on injection/security violations.
        """
        # 1. Security sanitization
        cleaned_prompt, _warnings = sanitize_prompt(prompt)

        # 2. Resolve provider / model / token cap
        pname = (provider_name or AIService._get_provider_name()).lower()
        mdl = model or AIService._get_model()
        cap = max_tokens or AIService._get_max_tokens()

        # 3. Trigger before_ai_request hook — plugins may mutate prompt
        from app.services.hook_service import HookService
        hook_results = HookService.trigger_hook(
            'before_ai_request', prompt=cleaned_prompt, provider=pname, model=mdl
        )
        # If a hook returns a non-None string, use it as the prompt override
        for result in hook_results:
            if isinstance(result, str):
                cleaned_prompt = result
                break

        # 4. Dispatch to provider (fall back to stub on unknown)
        provider_cls = _PROVIDERS.get(pname, StubProvider)
        response, tokens = provider_cls.generate(cleaned_prompt, max_tokens=cap, model=mdl)

        # 5. Trigger after_ai_response hook
        HookService.trigger_hook(
            'after_ai_response', prompt=cleaned_prompt, response=response, tokens_used=tokens
        )

        logger.debug('[AIService] provider=%s tokens=%d', pname, tokens)
        return response, tokens, pname

    @staticmethod
    def count_tokens(text: str) -> int:
        """Rough token estimate: 1 token ≈ 4 characters."""
        return max(1, len(text) // 4)

    @staticmethod
    def get_token_usage_stats() -> dict:
        """Aggregate token usage across all AI tables."""
        try:
            from app.models.ai_hint_request import AIHintRequest
            from app.models.ai_writeup import AIWriteup
            from app.models.ai_difficulty_prediction import AIDifficultyPrediction
            from app.models.ai_conversation import AIConversation
            from app.extensions import db

            hint_tokens = db.session.query(
                db.func.coalesce(db.func.sum(AIHintRequest.tokens_used), 0)
            ).scalar()
            writeup_tokens = db.session.query(
                db.func.coalesce(db.func.sum(AIWriteup.tokens_used), 0)
            ).scalar()
            pred_tokens = db.session.query(
                db.func.coalesce(db.func.sum(AIDifficultyPrediction.tokens_used), 0)
            ).scalar()
            conv_tokens = db.session.query(
                db.func.coalesce(db.func.sum(AIConversation.tokens_used), 0)
            ).scalar()

            return {
                'hint_tokens': int(hint_tokens),
                'writeup_tokens': int(writeup_tokens),
                'prediction_tokens': int(pred_tokens),
                'conversation_tokens': int(conv_tokens),
                'total_tokens': int(hint_tokens + writeup_tokens + pred_tokens + conv_tokens),
            }
        except Exception as exc:
            logger.warning('[AIService] Token stats failed: %s', exc)
            return {'hint_tokens': 0, 'writeup_tokens': 0,
                    'prediction_tokens': 0, 'conversation_tokens': 0, 'total_tokens': 0}
