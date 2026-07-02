"""
YARA Rule Service — Phase 18 SOC Platform / Detection Engineering.
Manage, validate and simulate testing of YARA rules (simulation only).
No real YARA library required — uses regex-based structural validation.
"""
import re
from app.extensions import db
from app.models.yara_rule import YaraRule


# Minimal YARA structural pattern: rule <name> { ... }
_YARA_STRUCTURE_RE = re.compile(
    r'rule\s+\w[\w_]*\s*(\:\s*[\w\s]+)?\s*\{.*?(strings\s*:\s*.+?)?(condition\s*:\s*.+?)\}',
    re.DOTALL | re.IGNORECASE
)


class YaraService:

    # -------------------------------------------------------------------------
    # Rule Management
    # -------------------------------------------------------------------------

    @staticmethod
    def create_rule(name: str, rule_text: str, description: str = '',
                    author: str = 'unknown', org_id: int = None) -> YaraRule:
        """Create and auto-validate a YARA rule."""
        rule = YaraRule(
            name=name,
            description=description,
            author=author,
            rule_text=rule_text,
            organization_id=org_id,
        )
        valid, error = YaraService.validate_rule(rule_text)
        rule.is_valid = valid
        rule.validation_error = error
        if valid:
            rule.status = 'testing'

        db.session.add(rule)
        db.session.commit()
        return rule

    @staticmethod
    def get_rule(rule_id: int) -> YaraRule:
        return db.session.get(YaraRule, rule_id)

    @staticmethod
    def list_rules(org_id: int = None, status: str = None):
        q = YaraRule.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        if status:
            q = q.filter_by(status=status)
        return q.order_by(YaraRule.created_at.desc()).all()

    # -------------------------------------------------------------------------
    # Validation (structural, no YARA binary)
    # -------------------------------------------------------------------------

    @staticmethod
    def validate_rule(rule_text: str) -> tuple:
        """
        Validate YARA rule structure using regex.
        Returns (is_valid: bool, error_message: str|None).
        """
        if not rule_text or not rule_text.strip():
            return False, "Rule text is empty"

        if 'rule ' not in rule_text:
            return False, "Missing 'rule' keyword"

        if 'condition:' not in rule_text and 'condition :' not in rule_text:
            return False, "Missing 'condition:' section"

        if not _YARA_STRUCTURE_RE.search(rule_text):
            return False, "Rule does not match expected YARA structure: rule <name> { condition: ... }"

        # Check for balanced braces
        opens = rule_text.count('{')
        closes = rule_text.count('}')
        if opens != closes:
            return False, f"Unbalanced braces: {opens} opening, {closes} closing"

        return True, None

    # -------------------------------------------------------------------------
    # Rule Testing (simulated)
    # -------------------------------------------------------------------------

    @staticmethod
    def test_rule(rule_id: int, sample_data: str) -> dict:
        """
        Simulate testing a YARA rule against sample data/artifact content.
        Extracts string patterns from rule and checks for presence in sample.
        """
        rule = db.session.get(YaraRule, rule_id)
        if not rule:
            return {'matched': False, 'error': 'Rule not found'}
        if not rule.is_valid:
            return {'matched': False, 'error': f'Rule is invalid: {rule.validation_error}'}

        # Extract string literals from YARA rule (simple regex)
        string_patterns = re.findall(r'"([^"]+)"', rule.rule_text)
        hex_patterns = re.findall(r'\{([0-9A-Fa-f\s]+)\}', rule.rule_text)

        matched_strings = []
        for pattern in string_patterns:
            if pattern.lower() in sample_data.lower():
                matched_strings.append(pattern)

        matched = bool(matched_strings)
        if matched:
            rule.hit_count += 1
            db.session.commit()

        return {
            'matched': matched,
            'rule_id': rule_id,
            'rule_name': rule.name,
            'matched_strings': matched_strings,
            'patterns_checked': len(string_patterns),
        }

    # -------------------------------------------------------------------------
    # Tagging
    # -------------------------------------------------------------------------

    @staticmethod
    def tag_rule(rule_id: int, tags: list) -> YaraRule:
        rule = db.session.get(YaraRule, rule_id)
        if not rule:
            raise ValueError(f"YARA rule {rule_id} not found")
        existing = set(t.strip() for t in rule.tags.split(',') if t.strip())
        existing.update(tags)
        rule.tags = ','.join(sorted(existing))
        db.session.commit()
        return rule
