"""
AI Blueprint — REST API Endpoints.

POST /api/v1/ai/hint          — request a progressive AI hint
POST /api/v1/ai/recommend     — get personalised challenge recommendations
POST /api/v1/ai/chat          — free-form AI chat (challenge-scoped or general)
GET  /api/v1/ai/writeup/<id>  — fetch a published writeup for a challenge
"""
from flask import request, jsonify
from flask_login import current_user, login_required
from app.ai import ai_bp
from app.utils.decorators import require_login


@ai_bp.route('/hint', methods=['POST'])
@require_login
def ai_hint():
    """Request a progressive AI hint (level 1, 2, or 3) for a challenge."""
    data = request.get_json(silent=True) or {}
    challenge_id = data.get('challenge_id')
    level = int(data.get('level', 1))

    if not challenge_id:
        return jsonify({'error': 'challenge_id is required.'}), 400

    from app.models.challenge import Challenge
    challenge = Challenge.query.filter_by(id=challenge_id, visible=True).first()
    if not challenge:
        return jsonify({'error': 'Challenge not found.'}), 404

    from app.services.hint_ai_service import HintAIService
    result = HintAIService.generate_hint(challenge, current_user, level=level)

    if result.get('error'):
        return jsonify({'error': result['error']}), 429

    return jsonify({
        'hint': result['response'],
        'level': result['level'],
        'tokens_used': result['tokens_used'],
        'cost_deducted': result['cost_deducted'],
    }), 200


@ai_bp.route('/recommend', methods=['POST'])
@require_login
def ai_recommend():
    """Get AI-powered challenge recommendations for the current user."""
    data = request.get_json(silent=True) or {}
    limit = min(int(data.get('limit', 5)), 10)

    from app.services.recommender_service import RecommenderService
    recommendations = RecommenderService.recommend(current_user, limit=limit)

    return jsonify({'recommendations': recommendations}), 200


@ai_bp.route('/chat', methods=['POST'])
@require_login
def ai_chat():
    """Free-form AI chat, optionally scoped to a specific challenge."""
    data = request.get_json(silent=True) or {}
    prompt = (data.get('prompt') or '').strip()
    challenge_id = data.get('challenge_id')

    if not prompt:
        return jsonify({'error': 'prompt is required.'}), 400

    if len(prompt) > 2000:
        return jsonify({'error': 'Prompt too long (max 2000 chars).'}), 400

    from app.services.ai_service import AIService, sanitize_prompt
    from app.models.ai_conversation import AIConversation
    from app.extensions import db

    try:
        clean_prompt, _ = sanitize_prompt(prompt)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    # Add system context if challenge-scoped
    if challenge_id:
        from app.models.challenge import Challenge
        ch = Challenge.query.filter_by(id=challenge_id, visible=True).first()
        if ch:
            ctx = (
                f"You are a CTF assistant helping with the challenge '{ch.title}' "
                f"(category: {ch.category.name if ch.category else 'Unknown'}). "
                f"Never reveal flags or full solutions.\n\n"
            )
            clean_prompt = ctx + clean_prompt

    try:
        response, tokens, provider = AIService.generate(clean_prompt, max_tokens=400)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    record = AIConversation(
        user_id=current_user.id,
        challenge_id=challenge_id,
        prompt=prompt,
        response=response,
        tokens_used=tokens,
        provider=provider,
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({'response': response, 'tokens_used': tokens}), 200


@ai_bp.route('/writeup/<int:challenge_id>', methods=['GET'])
@require_login
def ai_writeup(challenge_id: int):
    """Fetch the latest published writeup for a challenge."""
    from app.services.writeup_service import WriteupService
    result = WriteupService.get_published(challenge_id)
    if not result:
        return jsonify({'error': 'No published writeup available for this challenge.'}), 404
    return jsonify(result), 200
