from app.extensions import db
from app.models.skill import Skill, UserSkill, MASTERY_LEVELS

SKILLS_CATALOG = [
    {'slug': 'web_security', 'name': 'Web Security', 'category': 'web_security', 'icon': '🌐', 'description': 'Exploiting and securing web application vulnerabilities.'},
    {'slug': 'cryptography', 'name': 'Cryptography', 'category': 'cryptography', 'icon': '🔑', 'description': 'Analyzing and implementing cryptographic protocols.'},
    {'slug': 'reverse_engineering', 'name': 'Reverse Engineering', 'category': 'reverse_engineering', 'icon': '⚙️', 'description': 'Analyzing binary files and compiling source reconstruction.'},
    {'slug': 'forensics', 'name': 'Digital Forensics', 'category': 'forensics', 'icon': '🔍', 'description': 'Analyzing disk images, memory dumps, and network captures.'},
    {'slug': 'osint', 'name': 'OSINT', 'category': 'osint', 'icon': '📡', 'description': 'Open-source intelligence gathering and analysis.'},
    {'slug': 'cloud_security', 'name': 'Cloud Security', 'category': 'cloud_security', 'icon': '☁️', 'description': 'Securing cloud infrastructure, containers, and pipelines.'},
    {'slug': 'incident_response', 'name': 'Incident Response', 'category': 'incident_response', 'icon': '🚨', 'description': 'Handling, triaging, and responding to cyber incidents.'},
    {'slug': 'threat_hunting', 'name': 'Threat Hunting', 'category': 'threat_hunting', 'icon': '🏹', 'description': 'Proactively hunting for adversaries in network logs.'},
    {'slug': 'malware_analysis', 'name': 'Malware Analysis', 'category': 'malware_analysis', 'icon': '☣️', 'description': 'Analyzing malicious software behavior and payloads.'},
    {'slug': 'red_team', 'name': 'Red Teaming', 'category': 'red_team', 'icon': '⚔️', 'description': 'Adversarial simulation and active penetration testing.'},
    {'slug': 'blue_team', 'name': 'Blue Teaming', 'category': 'blue_team', 'icon': '🛡️', 'description': 'Defensive operations, detection engineering, and monitoring.'},
]

class SkillService:
    @staticmethod
    def seed_skills():
        """Seed predefined skills if database table is empty."""
        if Skill.query.first():
            return
        for item in SKILLS_CATALOG:
            s = Skill(**item)
            db.session.add(s)
        db.session.commit()

    @staticmethod
    def get_skill(slug: str) -> Skill:
        SkillService.seed_skills()
        return Skill.query.filter_by(slug=slug).first()

    @staticmethod
    def add_xp(user_id: int, skill_slug: str, xp_amount: int) -> UserSkill:
        """Add XP to a user's skill and dynamically recalculate level/mastery."""
        SkillService.seed_skills()
        skill = Skill.query.filter_by(slug=skill_slug).first()
        if not skill:
            raise ValueError(f"Skill with slug '{skill_slug}' does not exist.")

        us = UserSkill.query.filter_by(user_id=user_id, skill_id=skill.id).first()
        if not us:
            us = UserSkill(user_id=user_id, skill_id=skill.id, xp=0, level=1, mastery='novice')
            db.session.add(us)

        us.xp += xp_amount
        
        # Recalculate level: level = 1 + (xp // 100), max 10
        new_level = min(10, 1 + (us.xp // 100))
        us.level = new_level

        # Calculate mastery based on level
        # 1-2: novice, 3-4: beginner, 5-6: intermediate, 7-8: advanced, 9-10: expert
        if new_level <= 2:
            us.mastery = 'novice'
        elif new_level <= 4:
            us.mastery = 'beginner'
        elif new_level <= 6:
            us.mastery = 'intermediate'
        elif new_level <= 8:
            us.mastery = 'advanced'
        else:
            us.mastery = 'expert'

        db.session.commit()
        return us

    @staticmethod
    def get_user_skills(user_id: int) -> list[UserSkill]:
        SkillService.seed_skills()
        return UserSkill.query.filter_by(user_id=user_id).all()
