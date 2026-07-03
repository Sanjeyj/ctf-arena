"""
Navigator Service - Phase 19 Security Research & CTI Platform.
Computes tactic heatmaps, rule/detection coverages, and attack matrices.
"""
from app.models.sigma_rule import SigmaRule
from app.models.yara_rule import YaraRule
from app.models.yara_repository import YaraRepository
from app.models.sigma_repository import SigmaRepository
from app.models.hunt import Hunt
from app.models.attack_navigator import AttackNavigator
from app.extensions import db
import json

class NavigatorService:

    @staticmethod
    def compute_coverage(org_id: int = None) -> dict:
        """
        Compute tactic coverage, detection coverage, hunt coverage, and signature coverages.
        Generates simulated heatmaps and matrices representation.
        """
        # Count rules and hunts
        sigma_count = SigmaRule.query.count()
        yara_count = YaraRule.query.count()
        yara_repo_count = YaraRepository.query.count()
        sigma_repo_count = SigmaRepository.query.count()
        hunt_count = db.session.query(Hunt).count()

        # Define 12 standard MITRE ATT&CK Tactics
        tactics = [
            "Initial Access", "Execution", "Persistence", "Privilege Escalation",
            "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement",
            "Collection", "Command and Control", "Exfiltration", "Impact"
        ]

        # Calculate a mock coverage mapping per tactic (0 to 100 score)
        heatmap = {}
        for idx, tactic in enumerate(tactics):
            # Seed deterministic scores based on existing rule counts
            score = min(100, int((sigma_count * 15) + (yara_count * 10) + (idx * 7) + 5))
            heatmap[tactic] = {
                "score": score,
                "color": "#10b981" if score > 75 else "#f59e0b" if score > 40 else "#ef4444",
                "rules_count": int(score / 10)
            }

        # Calculate percentages
        tactic_pct = round(sum(h["score"] for h in heatmap.values()) / len(tactics), 2)
        detection_pct = min(100.0, round((sigma_count + yara_count) * 8.5, 2))
        hunt_pct = min(100.0, round(hunt_count * 12.0, 2))

        # Overall coverage metrics
        coverage = {
            "tactic_coverage_pct": tactic_pct,
            "detection_coverage_pct": detection_pct,
            "hunt_coverage_pct": hunt_pct,
            "yara_coverage_pct": min(100.0, round(yara_repo_count * 15.0, 2)),
            "sigma_coverage_pct": min(100.0, round(sigma_repo_count * 15.0, 2)),
            "counts": {
                "sigma_rules": sigma_count,
                "yara_rules": yara_count,
                "yara_repository": yara_repo_count,
                "sigma_repository": sigma_repo_count,
                "hunts": hunt_count
            },
            "heatmap": heatmap
        }

        # Auto-save or update layer in database
        layer_name = "default_coverage_layer"
        layer = AttackNavigator.query.filter_by(layer_name=layer_name).first()
        if not layer:
            layer = AttackNavigator(
                layer_name=layer_name,
                layer_json=json.dumps(coverage),
                organization_id=org_id
            )
            db.session.add(layer)
        else:
            layer.layer_json = json.dumps(coverage)
        db.session.commit()

        return coverage
