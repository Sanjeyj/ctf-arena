import datetime
from app.extensions import db, utcnow

class DockerImage(db.Model):
    __tablename__ = 'docker_images'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tag = db.Column(db.String(50), default='latest', nullable=False)
    registry = db.Column(db.String(255), nullable=True)  # e.g. 'ghcr.io/org' — None = DockerHub
    description = db.Column(db.Text, nullable=True)
    dockerfile_path = db.Column(db.String(255), nullable=True)
    compose_path = db.Column(db.String(255), nullable=True)
    default_port = db.Column(db.Integer, default=80, nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    instances = db.relationship('ChallengeInstance', backref='docker_image', lazy=True, cascade='all, delete-orphan')

    @property
    def full_ref(self) -> str:
        """Return the fully-qualified image reference, e.g. 'ghcr.io/org/pwn:latest'."""
        if self.registry:
            return f'{self.registry.rstrip("/")}/{self.name}:{self.tag}'
        return f'{self.name}:{self.tag}'
