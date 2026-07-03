"""
AttackNavigator model - Phase 19 Security Research & CTI Platform.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class AttackNavigator(db.Model, TimestampMixin, TenantMixin):
    """MITRE ATT&CK Navigator matrix/layer representation."""
    __tablename__ = 'attack_navigators'

    id = db.Column(db.Integer, primary_key=True)
    layer_name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    layer_json = db.Column(db.Text, nullable=False) # JSON-serialized layer representation

    def __repr__(self):
        return f'<AttackNavigator {self.layer_name!r}>'

    def to_dict(self):
        try:
            layer = json.loads(self.layer_json) if self.layer_json else {}
        except Exception:
            layer = {}
        return {
            'id': self.id,
            'layer_name': self.layer_name,
            'layer': layer,
            'organization_id': self.organization_id
        }
