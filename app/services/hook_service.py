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
    # Unified Cyber Defense Universe (Phase 30)
    'before_universe_simulation': 'Fired before a defense universe simulation run starts. kwargs: scenario, universe.',
    'after_universe_simulation': 'Fired after a defense universe simulation run ends. kwargs: simulation, outcome.',
    'before_posture_fusion': 'Fired before posture fusion scores computation. kwargs: universe.',
    'after_posture_fusion': 'Fired after posture fusion scores computation. kwargs: universe, score.',
    # Cyber Platform Control Plane (Phase 31)
    'before_policy_evaluation': 'Fired before control policy rules evaluation. kwargs: policy, context.',
    'after_policy_evaluation': 'Fired after control policy rules evaluation. kwargs: policy, result.',
    'before_model_governance_check': 'Fired before model safety governance checks. kwargs: record.',
    'after_model_governance_check': 'Fired after model safety governance checks. kwargs: record, score.',
    'before_change_simulation': 'Fired before change request execution. kwargs: change.',
    'after_change_simulation': 'Fired after change request execution. kwargs: change, outcome.',
    # Cyber Trust, Assurance & Verification Fabric (Phase 32)
    'before_trust_decision': 'Fired before ZT trust evaluation starts. kwargs: identity, device.',
    'after_trust_decision': 'Fired after ZT trust evaluation completes. kwargs: decision.',
    'before_assurance_evaluation': 'Fired before assurance case score computation. kwargs: assurance_case.',
    'after_assurance_evaluation': 'Fired after assurance case score computation. kwargs: assurance_case, confidence.',
    'before_control_validation': 'Fired before control validation run execution. kwargs: reference.',
    'after_control_validation': 'Fired after control validation run execution. kwargs: validation.',
    # Cyber Platform Observability, Reliability & Operations Fabric (Phase 33)
    'before_telemetry_ingest': 'Fired before telemetry ingest. kwargs: source_id, metric_name, metric_type, metric_value, unit, dimensions_json, org_id.',
    'after_telemetry_ingest': 'Fired after telemetry ingest. kwargs: metric.',
    'before_health_evaluation': 'Fired before health evaluation. kwargs: platform_service_id, availability, latency_ms, error_rate, saturation, org_id.',
    'after_health_evaluation': 'Fired after health evaluation. kwargs: snapshot.',
    'before_chaos_simulation': 'Fired before chaos simulation. kwargs: name, experiment_type, target_service, hypothesis, simulation_parameters_json, org_id.',
    'after_chaos_simulation': 'Fired after chaos simulation. kwargs: experiment.',
    'before_incident_correlation': 'Fired before incident correlation. kwargs: title, severity, source_module, affected_services_list, root_cause_summary, impact_summary, org_id.',
    'after_incident_correlation': 'Fired after incident correlation. kwargs: incident.',
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
