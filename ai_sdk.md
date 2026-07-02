# CTF Arena AI SDK

Developer guide for integrating with and extending the AI Challenge Assistant (Phase 14).

---

## Overview

CTF Arena v2 ships with a built-in AI Assistant that provides:

| Feature | Endpoint / Service |
|---|---|
| Progressive Hints | `POST /api/v1/ai/hint` |
| Challenge Recommendations | `POST /api/v1/ai/recommend` |
| Free-form Chat | `POST /api/v1/ai/chat` |
| Educational Writeups | `GET /api/v1/ai/writeup/<challenge_id>` |
| Difficulty Prediction | Admin `/admin/ai/predict/<challenge_id>` |

---

## Configuring a Provider

Providers are selected from the Admin Dashboard at **`/admin/ai`** or via the `Setting` table.

| Setting Key | Default | Description |
|---|---|---|
| `AI_PROVIDER` | `stub` | Active provider: `stub`, `ollama`, `openai`, `anthropic`, `gemini` |
| `AI_MODEL` | `stub-v1` | Model name forwarded to the provider |
| `MAX_AI_TOKENS` | `512` | Hard token cap per request |
| `AI_HINT_COST` | `0` | Points deducted per hint level (0 = free) |
| `AI_MAX_HINTS` | `3` | Maximum AI hints a user may request per challenge |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama base URL |
| `OPENAI_API_KEY` | _(empty)_ | OpenAI API key |
| `ANTHROPIC_API_KEY` | _(empty)_ | Anthropic API key |
| `GEMINI_API_KEY` | _(empty)_ | Google Gemini API key |

### Local Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a coding-focused model
ollama pull qwen2.5-coder:7b

# Verify
ollama run qwen2.5-coder:7b "Say hello"
```

Then in Admin → AI: set `AI_PROVIDER=ollama`, `AI_MODEL=qwen2.5-coder:7b`, `OLLAMA_URL=http://localhost:11434`.

### OpenAI Setup

In Admin → AI: set `AI_PROVIDER=openai`, `AI_MODEL=gpt-4o-mini`, paste your `OPENAI_API_KEY`.

---

## Plugin Hook Integration

Plugins can intercept every AI request and response using the **Hook Engine** (Phase 13).

### Available AI Hooks

| Hook Name | When Fired | kwargs |
|---|---|---|
| `before_ai_request` | Before any AI generation | `prompt`, `provider`, `model` |
| `after_ai_response` | After AI generation completes | `prompt`, `response`, `tokens_used` |
| `before_hint_generate` | Before a hint is generated | `challenge`, `user`, `level` |
| `after_hint_generate` | After a hint is generated | `challenge`, `user`, `level`, `response` |

### Hook Registration

Register hooks in your plugin's `plugin.py` or `routes.py`:

```python
from app.services.hook_service import HookService

def log_ai_usage(prompt, response, tokens_used):
    print(f"[MyPlugin] AI used {tokens_used} tokens")

HookService.register_hook('after_ai_response', log_ai_usage)
```

### Mutating Prompts (before_ai_request)

A `before_ai_request` callback can return a string to **override** the prompt:

```python
def add_context(prompt, provider, model):
    return f"Context: This is a CTF platform.\n\n{prompt}"

HookService.register_hook('before_ai_request', add_context)
```

> **Note**: Only the first non-None string return value is used as the override.

### Filtering Responses (after_ai_response)

```python
def audit_response(prompt, response, tokens_used):
    if 'flag{' in response.lower():
        # Log suspicious response
        import logging
        logging.getLogger(__name__).warning("AI may have leaked a flag!")

HookService.register_hook('after_ai_response', audit_response)
```

---

## Calling AIService Directly

Plugin code can call `AIService.generate()` for custom AI features:

```python
from app.services.ai_service import AIService, sanitize_prompt

# Always sanitize user input first
clean, warnings = sanitize_prompt(user_input)

# Generate with the configured provider
response, tokens, provider = AIService.generate(
    clean,
    max_tokens=200,  # optional override
)
```

---

## Using Domain Services

### HintAIService

```python
from app.services.hint_ai_service import HintAIService

result = HintAIService.generate_hint(challenge, user, level=2)
# result = {'response': '...', 'tokens_used': 87, 'level': 2, 'cost_deducted': 0, 'error': None}
```

### DifficultyService

```python
from app.services.difficulty_service import DifficultyService

prediction = DifficultyService.predict(challenge)
# prediction = {'predicted_difficulty': 'Hard', 'confidence': 0.85, 'explanation': '...', ...}
```

### WriteupService

```python
from app.services.writeup_service import WriteupService

result = WriteupService.generate(challenge, requesting_user=current_user)
# result = {'writeup_id': 3, 'status': 'draft', 'summary': '...', ...}
```

### RecommenderService

```python
from app.services.recommender_service import RecommenderService

recs = RecommenderService.recommend(user, limit=5)
# recs = [{'id': 12, 'title': 'XSS Lab', 'difficulty': 'Medium', 'score': 2.3}, ...]
```

---

## REST API Reference

All endpoints require an authenticated session (cookie-based login).

### `POST /api/v1/ai/hint`

```json
Request:  { "challenge_id": 5, "level": 2 }
Response: { "hint": "Focus on the HTTP request headers...", "level": 2, "tokens_used": 87, "cost_deducted": 0 }
```

### `POST /api/v1/ai/recommend`

```json
Request:  { "limit": 5 }
Response: { "recommendations": [{"id": 12, "title": "XSS Lab", "difficulty": "Medium", "score": 2.3}] }
```

### `POST /api/v1/ai/chat`

```json
Request:  { "prompt": "What tools do I use for OSINT challenges?", "challenge_id": null }
Response: { "response": "For OSINT challenges...", "tokens_used": 120 }
```

### `GET /api/v1/ai/writeup/<challenge_id>`

```json
Response: { "id": 1, "summary": "...", "steps": "...", "learning_points": "...", "created_at": "..." }
```
