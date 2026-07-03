"""
KnowledgeArticle model - Phase 22 Security Knowledge Hub.
Stores versioned articles detailing SOC alerts mitigation guides and research papers.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class KnowledgeArticle(db.Model, TimestampMixin, TenantMixin):
    """Knowledge article entity."""
    __tablename__ = 'knowledge_articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False, unique=True, index=True)
    category = db.Column(db.String(80), default='SOC') # SOC, Malware, IR, CTI, Threat Hunting
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.Integer, default=1)
    tags_string = db.Column('tags', db.String(256), default='')

    def __repr__(self):
        return f'<KnowledgeArticle {self.title!r} category={self.category}>'

    def to_dict(self):
        tags_list = [t.strip() for t in self.tags_string.split(',')] if self.tags_string else []
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'content': self.content,
            'version': self.version,
            'tags': tags_list
        }
