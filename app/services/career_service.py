import uuid
from app.extensions import db
from app.models.career import Employer, Job, Resume
from app.models.skill import UserSkill
from app.models.badge import UserBadge

class CareerService:
    """Service to handle jobs, employer accounts, and resume matching."""

    @staticmethod
    def create_employer(name: str, website: str = None, description: str = None) -> Employer:
        emp = Employer(name=name, website=website, description=description, is_verified=False)
        db.session.add(emp)
        db.session.commit()
        return emp

    @staticmethod
    def verify_employer(employer_id: int) -> bool:
        emp = Employer.query.get(employer_id)
        if not emp:
            return False
        emp.is_verified = True
        db.session.commit()
        return True

    @staticmethod
    def post_job(employer_id: int, title: str, description: str,
                 location: str = None, remote: bool = False,
                 required_skills: list = None, required_badges: list = None) -> Job:
        job = Job(
            employer_id=employer_id,
            title=title,
            description=description,
            location=location,
            remote=remote,
            required_skills=required_skills or [],
            required_badges=required_badges or [],
            is_active=True
        )
        db.session.add(job)
        db.session.commit()
        return job

    @staticmethod
    def update_resume(user_id: int, headline: str, summary: str, public: bool = False) -> Resume:
        resume = Resume.query.filter_by(user_id=user_id).first()
        if not resume:
            resume = Resume(
                user_id=user_id,
                share_url=uuid.uuid4().hex[:16]
            )
            db.session.add(resume)
        resume.headline = headline
        resume.summary = summary
        resume.public = public
        db.session.commit()
        return resume

    @staticmethod
    def is_eligible_for_job(user_id: int, job_id: int) -> tuple[bool, str]:
        """Check if user meets job eligibility requirements (skills, badges)."""
        job = Job.query.get(job_id)
        if not job:
            return False, "Job not found."

        # Check required badges
        for req_badge in job.required_badges:
            # Check user badges
            from app.services.badge_service import BadgeService
            if not BadgeService.has_badge(user_id, req_badge):
                return False, f"Missing required badge: {req_badge}"

        # Check required skills
        # For simplicity, user must have the skill at level >= 2 to qualify
        for req_skill in job.required_skills:
            from app.models.skill import Skill
            s = Skill.query.filter_by(slug=req_skill).first()
            if not s:
                continue
            us = UserSkill.query.filter_by(user_id=user_id, skill_id=s.id).first()
            if not us or us.level < 2:
                return False, f"Missing required skill mastery for: {req_skill} (Need Level 2+)"

        return True, "Eligible"
