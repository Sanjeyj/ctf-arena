"""
Unit and Integration tests for Step 2 and Step 6 Reputation & Profiles.
"""
import pytest
import json
from app.extensions import db
from app.models.researcher_profile import ResearcherProfile
from app.models.vulnerability_report import VulnerabilityReport
from app.models.program import Program
from app.models.case import Case
from app.models.badge import UserBadge, Badge
from app.models.organization import Organization
from app.models.user import User
from app.services.researcher_service import ResearcherService
from app.services.reputation_service import ReputationService
from app.services.auth_service import hash_password
from app.research.routes import create_jwt

@pytest.fixture
def reputation_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(VulnerabilityReport).delete()
        db.session.query(Case).delete()
        db.session.query(UserBadge).delete()
        db.session.query(ResearcherProfile).delete()
        db.session.commit()

        org = Organization(name="Reput Org", slug="reput-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        user = User(username="reput_user", email="user@reput.net", password_hash=hash_password("reput123"))
        db.session.add(user)
        db.session.commit()

        profile = ResearcherService.get_or_create_profile(user.id, org_id=org.id)

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "reput_user"}, secret)

        yield {
            "org": org,
            "user": user,
            "profile": profile,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_researcher_profile_service(app, reputation_setup):
    """Test retrieving and updating profiles via ResearcherService."""
    with app.app_context():
        user = reputation_setup['user']
        org = reputation_setup['org']

        profile = ResearcherService.get_or_create_profile(user.id, org_id=org.id)
        assert profile.user_id == user.id
        assert profile.reputation == 0

        # Update profile bio & country
        updated = ResearcherService.update_profile(
            user.id,
            bio="Security Auditor",
            country="Germany",
            skills="Web, Reversing",
            social_links={"twitter": "@sec_auditor"}
        )
        assert updated.bio == "Security Auditor"
        assert updated.country == "Germany"
        assert "twitter" in json.loads(updated.social_links)

def test_reputation_tiers(app, reputation_setup):
    """Test reputation tier score consolidations."""
    with app.app_context():
        user = reputation_setup['user']
        org = reputation_setup['org']

        # Ensure baseline tier is Bronze
        rep = ReputationService.calculate_reputation(user.id)
        assert rep['total_points'] == 0
        assert rep['tier'] == "Bronze"

        # Update research points manually
        profile = ResearcherProfile.query.filter_by(user_id=user.id).first()
        profile.research_points = 120
        db.session.commit()

        # Recalculate
        rep = ReputationService.calculate_reputation(user.id)
        assert rep['total_points'] == 120
        assert rep['tier'] == "Silver"

        # Set to 600
        profile.research_points = 600
        db.session.commit()

        rep = ReputationService.calculate_reputation(user.id)
        assert rep['tier'] == "Platinum"

def test_reputation_and_researcher_apis(client, reputation_setup):
    """Test REST API routes for profile lookups and tiers."""
    headers = reputation_setup['headers']
    user = reputation_setup['user']

    # Test GET /api/v1/researchers
    resp = client.get('/api/v1/researchers', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['count'] == 1
    assert json.loads(resp.data)['researchers'][0]['username'] == "reput_user"

    # Test GET /api/v1/reputation?user_id=X
    resp = client.get(f'/api/v1/reputation?user_id={user.id}', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['reputation']['tier'] == "Bronze"


def test_reputation_tiers_gold_threshold(app, reputation_setup):
    """Test Gold tier boundary limit score calculation."""
    with app.app_context():
        user = reputation_setup['user']
        profile = ResearcherProfile.query.filter_by(user_id=user.id).first()
        profile.research_points = 250
        db.session.commit()
        
        rep = ReputationService.calculate_reputation(user.id)
        assert rep['tier'] == "Gold"


def test_reputation_tiers_diamond_threshold(app, reputation_setup):
    """Test Diamond tier boundary limit score calculation."""
    with app.app_context():
        user = reputation_setup['user']
        profile = ResearcherProfile.query.filter_by(user_id=user.id).first()
        profile.research_points = 1000
        db.session.commit()
        
        rep = ReputationService.calculate_reputation(user.id)
        assert rep['tier'] == "Diamond"


def test_reputation_missing_user_profile(app):
    """Test reputation lookup for non-existent user returns Bronze and 0 points."""
    with app.app_context():
        rep = ReputationService.calculate_reputation(9999)
        assert rep['points'] == 0
        assert rep['tier'] == "Bronze"


def test_researcher_ranking_recalculation(app, reputation_setup):
    """Test ranking recalculation list orders correctly by points."""
    with app.app_context():
        org = reputation_setup['org']
        user1 = reputation_setup['user']
        # Create second user
        user2 = User(username="reput_user_2", email="user2@reput.net", password_hash="hash")
        db.session.add(user2)
        db.session.commit()
        
        profile1 = ResearcherProfile.query.filter_by(user_id=user1.id).first()
        profile1.reputation = 200
        
        profile2 = ResearcherService.get_or_create_profile(user2.id, org_id=org.id)
        profile2.reputation = 400
        db.session.commit()
        
        ResearcherService.calculate_rankings()
        
        p1 = ResearcherProfile.query.filter_by(user_id=user1.id).first()
        p2 = ResearcherProfile.query.filter_by(user_id=user2.id).first()
        assert p2.ranking == 1
        assert p1.ranking == 2


def test_researcher_hall_of_fame_list(app, reputation_setup):
    """Test Hall of Fame lists only users with 100+ reputation points."""
    with app.app_context():
        user = reputation_setup['user']
        profile = ResearcherProfile.query.filter_by(user_id=user.id).first()
        profile.reputation = 150
        profile.hall_of_fame = True
        db.session.commit()
        
        fame_list = ResearcherService.list_hall_of_fame()
        assert len(fame_list) >= 1
        assert fame_list[0].user_id == user.id

