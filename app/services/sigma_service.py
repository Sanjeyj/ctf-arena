"""
Sigma Rule Service — Phase 18 SOC Platform / Detection Engineering.
Parse, validate, test, and manage Sigma detection rules (simulation only).
"""
import yaml
from app.extensions import db
from app.models.sigma_rule import SigmaRule


REQUIRED_SIGMA_KEYS = ['title', 'logsource', 'detection']


class SigmaService:

    # -------------------------------------------------------------------------
    # Rule Management
    # -------------------------------------------------------------------------

    @staticmethod
    def create_rule(title: str, detection_yaml: str, logsource: str = '',
                    description: str = '', author: str = 'unknown',
                    severity: str = 'medium', org_id: int = None) -> SigmaRule:
        """Create and auto-validate a Sigma rule."""
        rule = SigmaRule(
            title=title,
            description=description,
            author=author,
            logsource=logsource,
            detection_yaml=detection_yaml,
            severity=severity,
            organization_id=org_id,
        )
        # Validate immediately
        valid, error = SigmaService.validate_rule(detection_yaml)
        rule.is_valid = valid
        rule.validation_error = error
        if valid:
            rule.status = 'experimental'

        db.session.add(rule)
        db.session.commit()
        return rule

    @staticmethod
    def get_rule(rule_id: int) -> SigmaRule:
        return db.session.get(SigmaRule, rule_id)

    @staticmethod
    def list_rules(org_id: int = None, status: str = None):
        q = SigmaRule.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        if status:
            q = q.filter_by(status=status)
        return q.order_by(SigmaRule.created_at.desc()).all()

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    @staticmethod
    def validate_rule(yaml_text: str) -> tuple:
        """
        Validate a Sigma rule YAML string.
        Returns (is_valid: bool, error_message: str|None).
        """
        if not yaml_text or not yaml_text.strip():
            return False, "Rule YAML is empty"

        try:
            parsed = yaml.safe_load(yaml_text)
        except yaml.YAMLError as e:
            return False, f"YAML parse error: {e}"

        if not isinstance(parsed, dict):
            return False, "Rule must be a YAML mapping"

        missing = [k for k in REQUIRED_SIGMA_KEYS if k not in parsed]
        if missing:
            return False, f"Missing required keys: {missing}"

        detection = parsed.get('detection', {})
        if not isinstance(detection, dict):
            return False, "detection must be a mapping"

        if 'condition' not in detection:
            return False, "detection must contain a 'condition' key"

        return True, None

    # -------------------------------------------------------------------------
    # Rule Testing (simulated)
    # -------------------------------------------------------------------------

    @staticmethod
    def test_rule(rule_id: int, sample_event: dict) -> dict:
        """
        Simulate testing a Sigma rule against a sample event.
        Returns match result with explanation (no real log processing).
        """
        rule = db.session.get(SigmaRule, rule_id)
        if not rule:
            return {'matched': False, 'error': 'Rule not found'}
        if not rule.is_valid:
            return {'matched': False, 'error': f'Rule is invalid: {rule.validation_error}'}

        try:
            parsed = yaml.safe_load(rule.detection_yaml)
        except Exception:
            return {'matched': False, 'error': 'Failed to parse rule YAML'}

        detection = parsed.get('detection', {})
        # Simulated matching: look for keyword overlap between detection keywords and event fields
        matched = False
        matched_keys = []
        for key, val in detection.items():
            if key == 'condition':
                continue
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        for ev_val in sample_event.values():
                            if isinstance(ev_val, str) and item.lower() in ev_val.lower():
                                matched = True
                                matched_keys.append(item)
            elif isinstance(val, dict):
                for sub_k, sub_v in val.items():
                    if sub_k in sample_event:
                        matched = True
                        matched_keys.append(sub_k)

        if matched:
            rule.hit_count += 1
            db.session.commit()

        return {
            'matched': matched,
            'rule_id': rule_id,
            'rule_title': rule.title,
            'matched_keys': matched_keys,
            'severity': rule.severity,
        }

    # -------------------------------------------------------------------------
    # Tagging
    # -------------------------------------------------------------------------

    @staticmethod
    def tag_rule(rule_id: int, tags: list) -> SigmaRule:
        rule = db.session.get(SigmaRule, rule_id)
        if not rule:
            raise ValueError(f"Sigma rule {rule_id} not found")
        existing = set(t.strip() for t in rule.tags.split(',') if t.strip())
        existing.update(tags)
        rule.tags = ','.join(sorted(existing))
        db.session.commit()
        return rule
