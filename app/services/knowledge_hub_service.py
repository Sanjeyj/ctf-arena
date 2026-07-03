"""
KnowledgeHub Service - Phase 22 Security Knowledge Hub.
Indexes remediation documents and recommends articles based on category mapping.
"""
from app.extensions import db
from app.models.knowledge_article import KnowledgeArticle

class KnowledgeHubService:

    @staticmethod
    def search(query_str: str, org_id: int = None) -> list[KnowledgeArticle]:
        q = KnowledgeArticle.query.filter(
            (KnowledgeArticle.title.like(f"%{query_str}%")) |
            (KnowledgeArticle.content.like(f"%{query_str}%"))
        )
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()

    @staticmethod
    def version(article_id: int, new_content: str) -> KnowledgeArticle:
        art = db.session.get(KnowledgeArticle, article_id)
        if not art:
            raise ValueError(f"Article #{article_id} not found")
        art.content = new_content
        art.version += 1
        db.session.commit()
        return art

    @staticmethod
    def recommend(category_str: str, org_id: int = None) -> list[KnowledgeArticle]:
        q = KnowledgeArticle.query.filter_by(category=category_str)
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()
