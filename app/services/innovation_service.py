"""
InnovationService - Phase 28 Cyber Civilization Platform.
Tracks R&D progress, timelines, and priorities for innovation projects.
"""
from app.extensions import db
from app.models.innovation_project import InnovationProject


class InnovationService:
    @staticmethod
    def track(project_id: int, progress_delta: float) -> InnovationProject:
        """Update innovation project progress with boundary checks."""
        project = db.session.get(InnovationProject, project_id)
        if not project:
            return None
        project.progress = round(max(0.0, min(1.0, project.progress + progress_delta)), 10)
        db.session.commit()
        return project

    @staticmethod
    def forecast(project_id: int) -> float:
        """Estimate the timeline factor (remaining timeline score) for project delivery."""
        project = db.session.get(InnovationProject, project_id)
        if not project:
            return 999.9
        remaining = 1.0 - project.progress
        # Forecast time constant (simulation baseline constant)
        timeline_factor = remaining * 12.0  # mock value in months
        return round(timeline_factor, 1)

    @staticmethod
    def prioritize(org_id: int) -> list:
        """List active innovation projects sorted by progress ascending (highest priority to build next)."""
        return InnovationProject.query.filter_by(organization_id=org_id).order_by(
            InnovationProject.progress.asc()
        ).all()
