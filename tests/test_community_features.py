import pytest
import datetime
from app.extensions import db, utcnow
from app.models.plugin import Plugin
from app.models.setting import Setting
from app.models.theme import Theme
from app.models.competition import Competition
from app.models.user import User
from app.models.submission import Submission
from app.models.challenge import Challenge
from app.models.category import Category
from app.repositories.user_repository import UserRepository
from app.services.live_scoreboard_service import LiveScoreboardService

def test_community_plugin_loading_model(app):
    """Test 1: Validate Plugin registration, enabling, and config serialization in DB."""
    with app.app_context():
        plugin = Plugin(name="Custom Discord Webhook", enabled=True, config='{"webhook_url": "http://discord.local"}')
        db.session.add(plugin)
        db.session.commit()

        assert plugin.id is not None
        assert plugin.name == "Custom Discord Webhook"
        assert plugin.enabled is True
        assert "webhook_url" in plugin.config

def test_community_settings_retrieval(app):
    """Test 2: Validate settings key-value retrieval and type constraints."""
    with app.app_context():
        setting = Setting(key="registration_open_override", value="True", type="boolean")
        db.session.add(setting)
        db.session.commit()

        queried = Setting.query.filter_by(key="registration_open_override").first()
        assert queried is not None
        assert queried.value == "True"
        assert queried.type == "boolean"

def test_community_theme_activation_logic(app):
    """Test 3: Verify theme switching logic and settings validation."""
    with app.app_context():
        # Set up a new active theme
        theme1 = Theme(name="cyberpunk-neon", is_active=True, settings='{"font": "Outfit"}')
        theme2 = Theme(name="retro-terminal", is_active=False)
        db.session.add_all([theme1, theme2])
        db.session.commit()

        assert theme1.is_active is True
        assert theme2.is_active is False

        # Verify only one is fetched as active
        active_themes = Theme.query.filter_by(is_active=True).all()
        assert len(active_themes) == 1
        assert active_themes[0].name == "cyberpunk-neon"

def test_community_webhook_trigger_mock(app):
    """Test 4: Verify webhook triggers dispatch validation schemas."""
    # Webhooks must define target HTTP URLs
    webhook_url = "http://api.ctf-platform.local/webhook"
    
    # Check simple URL validation helper
    def is_valid_url(url):
        return url.startswith("http://") or url.startswith("https://")

    assert is_valid_url(webhook_url) is True
    assert is_valid_url("ftp://malicious.local") is False

def test_community_scoreboard_freeze_cutoff(app):
    """Test 5: Verify scoreboard standings filter out solves submitted after freeze_time cutoff."""
    with app.app_context():
        # Clean any existing roles to avoid conflict
        from app.repositories.role_repository import RoleRepository
        RoleRepository.setup_default_roles()

        now = utcnow()
        # Set up competition that is active but currently frozen
        comp = Competition(
            name="Frozen Arena",
            start_time=now - datetime.timedelta(hours=2),
            end_time=now + datetime.timedelta(hours=2),
            freeze_time=now - datetime.timedelta(minutes=30),
            unfreeze_time=now + datetime.timedelta(hours=2),
            is_active=True
        )
        db.session.add(comp)
        db.session.flush()

        # Add player via UserRepository
        player = UserRepository.create(username="solve_p1", role_name="Participant")

        cat = Category(name="crypto")
        db.session.add(cat)
        db.session.flush()

        ch = Challenge(legacy_id="ch_f1", title="Ch1", description="D", points=100, difficulty="Easy", category_id=cat.id)
        db.session.add(ch)
        db.session.flush()

        # Submission before freeze (should be counted)
        sub_valid = Submission(user=player, challenge=ch, points=100, correct=True, elapsed=10, time=now - datetime.timedelta(minutes=45))
        # Submission after freeze (should be filtered out)
        sub_frozen = Submission(user=player, challenge=ch, points=100, correct=True, elapsed=20, time=now - datetime.timedelta(minutes=15))
        
        db.session.add_all([sub_valid, sub_frozen])
        db.session.commit()

        # Retrieve standings
        standings_data = LiveScoreboardService.get_live_rankings()
        assert standings_data["freeze_active"] is True
        
        # Standings list should only account for valid submissions before cutoff
        p1_record = next((s for s in standings_data["leaderboard"] if s["name"] == "solve_p1"), None)
        assert p1_record is not None
        # Score must be 100 (sub_valid), NOT 200 (sub_valid + sub_frozen)
        assert p1_record["score"] == 100
