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

    # Security Architecture & Exposure Fabric (Phase 34)
    'before_zone_create': 'Fired before architecture zone creation. kwargs: name, zone_type, org_id.',
    'after_zone_create': 'Fired after architecture zone creation. kwargs: zone.',
    'before_exposure_evaluation': 'Fired before exposure score evaluation. kwargs: exposure_asset_id, finding_type, title, severity, likelihood, impact_score, confidence, status, source_type, org_id.',
    'after_exposure_evaluation': 'Fired after exposure score evaluation. kwargs: finding.',
    'before_attack_path_analysis': 'Fired before critical attack path evaluation. kwargs: source_id, target_id, path, risk_score, org_id.',
    'after_attack_path_analysis': 'Fired after critical attack path evaluation. kwargs: path_record.',
    'before_control_coverage_evaluation': 'Fired before control coverage mapping evaluation. kwargs: control_ref, resource_type, resource_id, coverage_score, effectiveness_score, status, org_id.',
    'after_control_coverage_evaluation': 'Fired after control coverage mapping evaluation. kwargs: map_record.',
    'before_remediation_prioritization': 'Fired before remediation plan prioritization. kwargs: title, finding_id, recommended_action, priority_score, org_id.',
    'after_remediation_prioritization': 'Fired after remediation plan prioritization. kwargs: plan_record.',

    # Continuous Security Validation & Defense Effectiveness Fabric (Phase 35)
    'before_validation_campaign': 'Fired before validation campaign creation. kwargs: name, description, campaign_type, scope, priority, scheduled_at, org_id.',
    'after_validation_campaign': 'Fired after validation campaign creation. kwargs: campaign_id, org_id.',
    'before_validation_execution': 'Fired before validation scenario execution. kwargs: scenario_id, org_id.',
    'after_validation_execution': 'Fired after validation scenario execution. kwargs: execution_id, org_id.',
    'before_detection_validation': 'Fired before detection validation runs. kwargs: execution_id, detection_type, detection_reference, synthetic_signal_type, expected_detection, org_id.',
    'after_detection_validation': 'Fired after detection validation runs. kwargs: validation_id, org_id.',
    'before_regression_evaluation': 'Fired before validation regression evaluation. kwargs: resource_type, resource_id, previous_score, current_score, org_id.',
    'after_regression_evaluation': 'Fired after validation regression evaluation. kwargs: regression_id, org_id.',

    # Cyber Risk Quantification (Phase 36)
    'before_risk_quantification': 'Fired before risk quantification starts. kwargs: scenario_id, org_id.',
    'after_risk_quantification': 'Fired after risk quantification finishes. kwargs: scenario_id, org_id, inherent_risk_score.',
    'before_loss_simulation': 'Fired before loss simulation run starts. kwargs: run_id, org_id.',
    'after_loss_simulation': 'Fired after loss simulation run ends. kwargs: run_id, org_id, expected_loss.',
    'before_investment_evaluation': 'Fired before security investment evaluation. kwargs: title, investment_category, cost, expected_loss_reduction, expected_risk_reduction, org_id.',
    'after_investment_evaluation': 'Fired after security investment evaluation. kwargs: investment_id, org_id, rosi_score.',
    'before_risk_appetite_check': 'Fired before appetite boundaries evaluation. kwargs: appetite_id, org_id.',
    'after_risk_appetite_check': 'Fired after appetite boundaries evaluation. kwargs: appetite_id, org_id, is_breached.',

    # Strategic Resilience Decision (Phase 37)
    'before_stress_test': 'Fired before resilience stress test run. kwargs: scenario_id, org_id.',
    'after_stress_test': 'Fired after resilience stress test run. kwargs: run_id, org_id.',
    'before_portfolio_optimization': 'Fired before portfolio optimization run. kwargs: plan_id, org_id.',
    'after_portfolio_optimization': 'Fired after portfolio optimization run. kwargs: plan_id, org_id.',
    'before_strategic_decision': 'Fired before strategic decision record evaluation. kwargs: title, org_id.',
    'after_strategic_decision': 'Fired after strategic decision record evaluation. kwargs: decision_id, org_id.',
    'before_resilience_plan_approval': 'Fired before resilience plan approval action. kwargs: plan_id, org_id.',
    'after_resilience_plan_approval': 'Fired after resilience plan approval action. kwargs: plan_id, org_id.',

    # Phase 38 — Enterprise Security Decision Intelligence,
    # Adaptive Policy Optimization & Governance Fabric
    'before_decision_recommendation': 'Fired before decision recommendation generation. kwargs: context_id, org_id.',
    'after_decision_recommendation': 'Fired after decision recommendation generation. kwargs: recommendation_id, org_id.',
    'before_policy_optimization': 'Fired before policy optimization run. kwargs: run_id, org_id.',
    'after_policy_optimization': 'Fired after policy optimization run. kwargs: run_id, org_id.',
    'before_governance_scoring': 'Fired before governance scoring. kwargs: org_id.',
    'after_governance_scoring': 'Fired after governance scoring. kwargs: scorecard_id, org_id.',
    'before_governance_drift_detection': 'Fired before governance drift detection. kwargs: org_id.',
    'after_governance_drift_detection': 'Fired after governance drift detection. kwargs: org_id.',

    # Phase 39 — Systemic Cyber Risk, Collective Resilience
    # & Federated Governance Fabric
    'before_systemic_risk_analysis': 'Fired before systemic risk analysis starts. kwargs: org_id.',
    'after_systemic_risk_analysis': 'Fired after systemic risk analysis completes. kwargs: org_id, metrics.',
    'before_contagion_simulation': 'Fired before contagion simulation starts. kwargs: scenario_id, org_id.',
    'after_contagion_simulation': 'Fired after contagion simulation completes. kwargs: run_id, org_id.',
    'before_collective_resilience_evaluation': 'Fired before collective resilience plan evaluation. kwargs: plan_id, org_id.',
    'after_collective_resilience_evaluation': 'Fired after collective resilience plan evaluation. kwargs: plan_id, org_id.',
    'before_federation_governance_decision': 'Fired before federation governance decision action. kwargs: record_id, org_id.',
    'after_federation_governance_decision': 'Fired after federation governance decision action. kwargs: record_id, org_id.',

    # Phase 40 — Platform Convergence, Certification,
    # Mission Control & Release Readiness
    'before_platform_certification': 'Fired before platform certification starts. kwargs: org_id, run_id.',
    'after_platform_certification': 'Fired after platform certification completes. kwargs: org_id, run_id, score.',
    'before_release_baseline': 'Fired before release baseline creation. kwargs: org_id, version, metrics.',
    'after_release_baseline': 'Fired after release baseline creation. kwargs: org_id, version, baseline_id.',
    'before_readiness_evaluation': 'Fired before readiness evaluation starts. kwargs: org_id, metric_type.',
    'after_readiness_evaluation': 'Fired after readiness evaluation completes. kwargs: org_id, metric_id, overall_score.',
    'before_release_gate_decision': 'Fired before release gate decision is registered. kwargs: org_id, baseline_id, gate_type.',
    'after_release_gate_decision': 'Fired after release gate decision is registered. kwargs: org_id, baseline_id, decision_id, decision.',
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
