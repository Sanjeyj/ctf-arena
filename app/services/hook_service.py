import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Documented hook registry — available to plugin authors (ai_sdk.md)
# ---------------------------------------------------------------------------

SUPPORTED_HOOKS = {
    # Challenge lifecycle
    'before_challenge_render': 'Fired before a challenge is rendered. kwargs: challenge, user.',
    'after_submission': 'Fired after a flag submission. kwargs: submission, correct, challenge, user.',
    'before_score_update': 'Fired before a score is updated. kwargs: user_id, points, challenge_id.',
    # Auth lifecycle
    'after_login': 'Fired after a successful login. kwargs: user.',
    # Team lifecycle
    'after_team_create': 'Fired after a team is created. kwargs: team.',
    # Docker lifecycle
    'before_container_start': 'Fired before a container starts. kwargs: challenge, user.',
    'after_container_stop': 'Fired after a container stops. kwargs: challenge, user, container_id.',
    # AI lifecycle (Phase 14)
    'before_ai_request': 'Fired before any AI generation. kwargs: prompt, provider, model. Return str to override prompt.',
    'after_ai_response': 'Fired after AI generation completes. kwargs: prompt, response, tokens_used.',
    'before_hint_generate': 'Fired before an AI hint is generated. kwargs: challenge, user, level.',
    'after_hint_generate': 'Fired after an AI hint is generated. kwargs: challenge, user, level, response.',
    # Cyber Range lifecycle (Phase 16)
    'before_attack_simulation': 'Fired before an AI attack step is simulated. kwargs: simulation, capability.',
    'after_attack_event': 'Fired after an AI attack event is generated. kwargs: event, simulation.',
    'before_defense_action': 'Fired before a defensive/SOC action is simulated. kwargs: event, soc_level.',
    'after_incident_close': 'Fired after an incident is resolved. kwargs: incident.',
    # Research and CTI lifecycle (Phase 19)
    'before_research_request': 'Fired before CTI research AI query is sent. kwargs: query.',
    'after_research_response': 'Fired after CTI research AI response is compiled. kwargs: query, response.',
}



class HookService:
    _hooks = {}

    @classmethod
    def register_hook(cls, hook_name, callback):
        """Register a callback function to a hook lifecycle checkpoint."""
        if hook_name not in cls._hooks:
            cls._hooks[hook_name] = []
        if callback not in cls._hooks[hook_name]:
            cls._hooks[hook_name].append(callback)
            logger.info(f"[HookService] Registered callback '{callback.__name__}' for hook '{hook_name}'")

    @classmethod
    def trigger_hook(cls, hook_name, *args, **kwargs):
        """Invoke all callbacks registered under the hook name, gathering their outputs."""
        results = []
        if hook_name in cls._hooks:
            for callback in cls._hooks[hook_name]:
                try:
                    res = callback(*args, **kwargs)
                    results.append(res)
                except Exception as e:
                    logger.error(f"[HookService] Error in hook '{hook_name}' callback '{callback.__name__}': {str(e)}", exc_info=True)
        return results

    @classmethod
    def fire(cls, hook_name, *args, **kwargs):
        """Alias for trigger_hook."""
        return cls.trigger_hook(hook_name, *args, **kwargs)

    @classmethod
    def remove_hook(cls, hook_name, callback):
        """Remove a previously registered callback from a hook list."""
        if hook_name in cls._hooks and callback in cls._hooks[hook_name]:
            cls._hooks[hook_name].remove(callback)
            logger.info(f"[HookService] Removed callback '{callback.__name__}' from hook '{hook_name}'")

    @classmethod
    def clear_all(cls):
        """Reset all hook registrations (mainly for clean test environments)."""
        cls._hooks.clear()

    @classmethod
    def list_hooks(cls) -> dict:
        """Return all supported hooks with descriptions."""
        return dict(SUPPORTED_HOOKS)
