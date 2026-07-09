import json
from app.extensions import db
from app.models.decision_context import DecisionContext
from app.models.decision_recommendation import DecisionRecommendation
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.resilience_portfolio_metric import ResiliencePortfolioMetric
from app.models.compliance_control import ComplianceControl


class DecisionIntelligenceService:
    @staticmethod
    def create_context(name, context_type, business_scope, org_id):
        # Validate context_type
        valid_types = ['risk', 'resilience', 'compliance', 'architecture', 'operations', 'investment', 'trust', 'incident']
        if context_type not in valid_types:
            raise ValueError(f"Invalid context type: {context_type}")

        # Gather signals
        signals = DecisionIntelligenceService.collect_context_signals(context_type, org_id)

        ctx = DecisionContext(
            name=name,
            context_type=context_type,
            business_scope=business_scope,
            risk_score=signals.get('risk_score', 50.0),
            resilience_score=signals.get('resilience_score', 50.0),
            control_effectiveness_score=signals.get('control_effectiveness_score', 50.0),
            evidence_confidence_score=signals.get('evidence_confidence_score', 50.0),
            urgency_score=signals.get('urgency_score', 50.0),
            context_json=json.dumps(signals),
            status='active',
            organization_id=org_id
        )
        db.session.add(ctx)
        db.session.commit()
        return ctx

    @staticmethod
    def collect_context_signals(context_type, org_id):
        # Fetch existing metric scores for integration points
        # Risk: Average of residual_risk_score
        scenarios = QuantitativeRiskScenario.query.filter_by(organization_id=org_id).all()
        risk_score = 50.0
        if scenarios:
            risk_score = sum(s.residual_risk_score for s in scenarios) / len(scenarios)

        # Resilience: latest portfolio metric
        resilience = ResiliencePortfolioMetric.query.filter_by(organization_id=org_id).order_by(ResiliencePortfolioMetric.id.desc()).first()
        resilience_score = 50.0
        if resilience:
            resilience_score = resilience.collective_resilience_score

        # Compliance: passed ratio
        controls = ComplianceControl.query.filter_by(organization_id=org_id).all()
        control_eff = 50.0
        if controls:
            passed = sum(1 for c in controls if c.status == 'passed')
            control_eff = (passed / len(controls)) * 100.0

        # Evidence confidence
        evidence_conf = 75.0

        # Urgency: weighted combination of poor scores
        urgency = max(0.0, min(100.0, (risk_score + (100.0 - resilience_score) + (100.0 - control_eff)) / 3.0))

        return {
            'risk_score': round(risk_score, 2),
            'resilience_score': round(resilience_score, 2),
            'control_effectiveness_score': round(control_eff, 2),
            'evidence_confidence_score': round(evidence_conf, 2),
            'urgency_score': round(urgency, 2)
        }

    @staticmethod
    def normalize_context(context_id, org_id):
        ctx = DecisionContext.query.filter_by(id=context_id, organization_id=org_id).first()
        if not ctx:
            return None
        ctx.risk_score = max(0.0, min(100.0, ctx.risk_score))
        ctx.resilience_score = max(0.0, min(100.0, ctx.resilience_score))
        ctx.control_effectiveness_score = max(0.0, min(100.0, ctx.control_effectiveness_score))
        ctx.evidence_confidence_score = max(0.0, min(100.0, ctx.evidence_confidence_score))
        ctx.urgency_score = max(0.0, min(100.0, ctx.urgency_score))
        db.session.commit()
        return ctx

    @staticmethod
    def calculate_priority(rec):
        # priority_score = (risk_red * 0.4) + (res_gain * 0.3) + (ctrl_imp * 0.3)
        # clamp between 0.0 and 100.0
        score = (rec.expected_risk_reduction * 0.4) + (rec.expected_resilience_gain * 0.3) + (rec.expected_control_improvement * 0.3)
        return max(0.0, min(100.0, score))

    @staticmethod
    def generate_recommendation(context_id, rec_type, title, description, expected_risk_red, expected_res_gain, expected_ctrl_imp, cost, confidence, org_id):
        ctx = DecisionContext.query.filter_by(id=context_id, organization_id=org_id).first()
        if not ctx:
            raise ValueError("Decision context not found or tenant mismatch")

        # Validate bounds
        if not (0.0 <= expected_risk_red <= 100.0) or not (0.0 <= expected_res_gain <= 100.0) or not (0.0 <= expected_ctrl_imp <= 100.0):
            raise ValueError("Scores must be between 0 and 100")
        if cost < 0.0:
            raise ValueError("Cost cannot be negative")

        rec = DecisionRecommendation(
            decision_context_id=context_id,
            recommendation_type=rec_type,
            title=title,
            description=description,
            expected_risk_reduction=expected_risk_red,
            expected_resilience_gain=expected_res_gain,
            expected_control_improvement=expected_ctrl_imp,
            estimated_cost=cost,
            confidence_score=confidence,
            status='generated',
            organization_id=org_id
        )
        rec.priority_score = DecisionIntelligenceService.calculate_priority(rec)
        db.session.add(rec)
        db.session.commit()
        return rec

    @staticmethod
    def rank_recommendations(context_id, org_id):
        return DecisionRecommendation.query.filter_by(
            decision_context_id=context_id, organization_id=org_id
        ).order_by(DecisionRecommendation.priority_score.desc()).all()

    @staticmethod
    def decision_summary(org_id):
        contexts = DecisionContext.query.filter_by(organization_id=org_id).all()
        recs = DecisionRecommendation.query.filter_by(organization_id=org_id).all()
        avg_urgency = sum(c.urgency_score for c in contexts) / len(contexts) if contexts else 0.0
        return {
            'total_contexts': len(contexts),
            'total_recommendations': len(recs),
            'average_urgency_score': round(avg_urgency, 2)
        }
