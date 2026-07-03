"""
Research Service - Phase 19 Security Research & CTI Platform.
Manages research reports creation, structure, validation, and curation.
"""
import json
from app.extensions import db
from app.models.research_report import ResearchReport

class ResearchService:

    @staticmethod
    def create_report(title: str, executive_summary: str = "",
                      technical_analysis: str = "", iocs: list = None,
                      mitre_techniques: list = None, recommendations: str = "",
                      author_id: int = None, org_id: int = None) -> ResearchReport:
        """Create a structured CTI research report."""
        report = ResearchReport(
            title=title,
            executive_summary=executive_summary,
            technical_analysis=technical_analysis,
            ioc_json=json.dumps(iocs or []),
            mitre_techniques_json=json.dumps(mitre_techniques or []),
            recommendations=recommendations,
            author_id=author_id,
            organization_id=org_id
        )
        db.session.add(report)
        db.session.commit()
        return report

    @staticmethod
    def get_report(report_id: int) -> ResearchReport:
        return db.session.get(ResearchReport, report_id)

    @staticmethod
    def list_reports(org_id: int = None):
        q = ResearchReport.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()

    @staticmethod
    def update_report(report_id: int, **kwargs) -> ResearchReport:
        report = db.session.get(ResearchReport, report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Serialize lists if passed directly
        if 'iocs' in kwargs:
            report.ioc_json = json.dumps(kwargs.pop('iocs'))
        if 'mitre_techniques' in kwargs:
            report.mitre_techniques_json = json.dumps(kwargs.pop('mitre_techniques'))
            
        for key, val in kwargs.items():
            if hasattr(report, key):
                setattr(report, key, val)
        db.session.commit()
        return report

    @staticmethod
    def delete_report(report_id: int) -> bool:
        report = db.session.get(ResearchReport, report_id)
        if not report:
            return False
        db.session.delete(report)
        db.session.commit()
        return True
