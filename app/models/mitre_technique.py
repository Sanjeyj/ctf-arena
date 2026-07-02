from app.extensions import db
from app.models.mixins import TimestampMixin

class MitreTechnique(db.Model, TimestampMixin):
    """
    Catalog of MITRE ATT&CK techniques used for mapping simulation events.
    """
    __tablename__ = 'mitre_techniques'

    id = db.Column(db.Integer, primary_key=True)
    tactic = db.Column(db.String(40), nullable=False, index=True)
    technique_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # e.g., T1566
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    mitigation = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<MitreTechnique {self.technique_id}: {self.name}>'
