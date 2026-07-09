"""
ValidationEngineService - Phase 35 Continuous Security Validation.
Simulates scenario execution runs, logs asserts/checks, and measures control effectiveness.
"""
from app.extensions import db
from app.models.validation_scenario import ValidationScenario
from app.models.validation_execution import ValidationExecution
from app.models.validation_check import ValidationCheck
from app.services.hook_service import HookService
import datetime
import json


class ValidationEngineService:
    @staticmethod
    def execute_scenario(scenario_id, org_id):
        scenario = ValidationScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return None

        # Hook triggers
        hook_results = HookService.trigger_hook(
            'before_validation_execution',
            scenario_id=scenario_id,
            org_id=org_id
        )

        exec_record = ValidationExecution(
            campaign_id=scenario.campaign_id,
            scenario_id=scenario_id,
            status='running',
            started_at=datetime.datetime.utcnow(),
            baseline_score=70.0,  # standard default baseline
            result_score=0.0,
            effectiveness_score=0.0,
            organization_id=org_id
        )
        db.session.add(exec_record)
        db.session.commit()

        # Run simulated checks
        score = 0.0
        passed_checks = 0
        total_checks = 2

        # Check 1: Simulating mock target validation check
        check1 = ValidationEngineService.create_check(
            exec_record.id, scenario.scenario_type, "mock_ref", 1,
            scenario.expected_outcome, scenario.expected_outcome, 100.0, "passed", None, org_id
        )
        passed_checks += 1

        # Check 2: Simulating configuration correctness check
        config = {}
        try:
            if scenario.configuration_json:
                config = json.loads(scenario.configuration_json)
        except Exception:
            pass

        check2_status = "passed"
        check2_score = 100.0
        actual_val = "valid_config"
        if config.get("fail_sim", False):
            check2_status = "failed"
            check2_score = 0.0
            actual_val = "failed_sim"

        check2 = ValidationEngineService.create_check(
            exec_record.id, scenario.scenario_type, "config_check", 2,
            "valid_config", actual_val, check2_score, check2_status, None, org_id
        )
        if check2_status == "passed":
            passed_checks += 1

        # Calculate scores
        score = (passed_checks / total_checks) * 100.0
        effectiveness = score / 100.0

        exec_record.status = 'completed'
        exec_record.completed_at = datetime.datetime.utcnow()
        exec_record.result_score = score
        exec_record.effectiveness_score = effectiveness
        exec_record.result_summary = f"Executed {total_checks} checks, {passed_checks} passed."
        db.session.commit()

        HookService.trigger_hook('after_validation_execution', execution_id=exec_record.id, org_id=org_id)
        return exec_record

    @staticmethod
    def create_check(execution_id, check_type, target_ref_type, target_ref_id, expected_result, actual_result, score, status, evidence_record_id, org_id):
        # Validate target ownership mock check
        check = ValidationCheck(
            execution_id=execution_id,
            check_type=check_type,
            target_reference_type=target_ref_type,
            target_reference_id=target_ref_id,
            expected_result=expected_result,
            actual_result=actual_result,
            score=score,
            status=status,
            evidence_record_id=evidence_record_id,
            organization_id=org_id
        )
        db.session.add(check)
        db.session.commit()
        return check

    @staticmethod
    def evaluate_expected_outcome(execution_id, org_id):
        exec_record = ValidationExecution.query.filter_by(id=execution_id, organization_id=org_id).first()
        if not exec_record:
            return False
        return exec_record.result_score >= exec_record.baseline_score

    @staticmethod
    def calculate_effectiveness(result_score, baseline_score):
        if not baseline_score:
            return 0.0
        ratio = result_score / baseline_score
        return min(1.0, max(0.0, ratio))

    @staticmethod
    def complete_execution(execution_id, result_score, summary, org_id):
        exec_record = ValidationExecution.query.filter_by(id=execution_id, organization_id=org_id).first()
        if not exec_record:
            return None
        exec_record.status = 'completed'
        exec_record.completed_at = datetime.datetime.utcnow()
        exec_record.result_score = result_score
        exec_record.effectiveness_score = min(1.0, max(0.0, result_score / 100.0))
        exec_record.result_summary = summary
        db.session.commit()
        return exec_record

    @staticmethod
    def execution_summary(execution_id, org_id):
        exec_record = ValidationExecution.query.filter_by(id=execution_id, organization_id=org_id).first()
        if not exec_record:
            return None
        checks = ValidationCheck.query.filter_by(execution_id=execution_id, organization_id=org_id).all()
        return {
            "execution_id": exec_record.id,
            "status": exec_record.status,
            "result_score": exec_record.result_score,
            "effectiveness_score": exec_record.effectiveness_score,
            "total_checks": len(checks),
            "passed_checks": sum(1 for c in checks if c.status == 'passed')
        }
