import pytest
import io
import os
import hashlib
from app.extensions import db
from app.models.challenge import Challenge
from app.models.category import Category
from app.models.flag import Flag
from app.models.hint import Hint
from app.models.challenge_file import ChallengeFile
from app.services.challenge_service import ChallengeService
from app.services.category_service import CategoryService
from app.services.flag_service import FlagService
from app.services.hint_service import HintService
from app.services.file_service import FileService
from app.services.scoring_service import ScoringService
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

@pytest.fixture(autouse=True)
def setup_roles_and_perms(app):
    with app.app_context():
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

def test_challenge_crud(app):
    """Verify challenge creation, updates, and soft deletes."""
    with app.app_context():
        cat, _ = CategoryService.create_category("Web Exp", "Web exploits", visible=True)
        
        ch = ChallengeService.create_challenge(
            legacy_id="ch_test",
            title="Test Challenge",
            description="Details",
            points=100,
            difficulty="Medium",
            category_id=cat.id,
            decay_type="linear",
            decay_rate=5,
            minimum_points=50
        )
        assert ch is not None
        assert ch.legacy_id == "ch_test"
        assert ch.points == 100
        assert ch.initial_points == 100
        assert ch.current_points == 100
        assert ch.minimum_points == 50

        # Update metadata
        updated = ChallengeService.update_challenge(ch.id, title="Test New Title", points=90)
        assert updated.title == "Test New Title"

        # Delete challenge
        success = ChallengeService.delete_challenge(ch.id)
        assert success is True
        
        # Verify soft deleted from default listings
        res = ChallengeService.get_challenge_by_any_id("ch_test")
        assert res is None

def test_category_crud(app):
    """Verify category creation unique constraints and CRUD updates."""
    with app.app_context():
        cat, err = CategoryService.create_category("Crypto", "Cryptography")
        assert err is None
        assert cat is not None

        # Duplicate check
        _, err = CategoryService.create_category("Crypto", "Duplicate")
        assert "already exists" in err

        # Update
        updated, _ = CategoryService.update_category(cat.id, description="New Description")
        assert updated.description == "New Description"

        # Delete
        success, _ = CategoryService.delete_category(cat.id)
        assert success is True

def test_multi_flags_evaluation(app):
    """Verify exact, case insensitive, regex, and hashed flags matching."""
    with app.app_context():
        ch = ChallengeService.create_challenge("ch_flag_test", "Flags Test", "Desc", 50, "Easy")
        
        f1, _ = FlagService.create_flag(ch.id, "FLAG{case_sensitive}", "exact", is_case_sensitive=True)
        f2, _ = FlagService.create_flag(ch.id, "FLAG{insensitive}", "exact", is_case_sensitive=False)
        f3, _ = FlagService.create_flag(ch.id, "FLAG{reg_.*}", "regex", is_case_sensitive=True)
        
        # Hashed flag: sha256 of "secret_flag" is 'e2794301...'
        hashed = hashlib.sha256(b"secret_flag").hexdigest()
        f4, _ = FlagService.create_flag(ch.id, hashed, "hashed")

        # Test matches
        assert FlagService.verify_flag(f1, "FLAG{case_sensitive}") is True
        assert FlagService.verify_flag(f1, "flag{case_sensitive}") is False # wrong case

        assert FlagService.verify_flag(f2, "FLAG{INSENSITIVE}") is True
        assert FlagService.verify_flag(f2, "flag{insensitive}") is True

        assert FlagService.verify_flag(f3, "FLAG{reg_pattern}") is True
        assert FlagService.verify_flag(f3, "FLAG{reg_123}") is True
        assert FlagService.verify_flag(f3, "WRONG{reg_12}") is False

        assert FlagService.verify_flag(f4, "secret_flag") is True
        assert FlagService.verify_flag(f4, "wrong_flag") is False

def test_hints_costs_and_unlock_tracking(app):
    """Verify hint points deduction and balance constraints checks."""
    with app.app_context():
        # Setup participant
        user, _ = AuthService.register_user("hint_player", "Password123!", "Password123!")
        
        ch = ChallengeService.create_challenge("ch_hint", "Hint Challenge", "Desc", 100, "Easy")
        hint1, _ = HintService.create_hint(ch.id, "Unlockable Hint", cost=30)

        # Unlock attempt without sufficient points (starts at 0)
        success, err = HintService.unlock_hint(hint1.id, user.id)
        assert success is False
        assert "Not enough points" in err

        # Award points to player by solving a challenge
        from app.repositories.submission_repository import SubmissionRepository
        SubmissionRepository.add_solve("hint_player", "ch_hint", points=100, elapsed=10)
        
        # Unlock attempt now - should succeed
        success, err = HintService.unlock_hint(hint1.id, user.id)
        assert success is True
        assert err is None

        # Verify hint cost is deducted from total score (100 - 30 = 70)
        from app.services.user_service import UserService
        profile = UserService.get_user_profile_data("hint_player")
        assert profile["total_score"] == 70

def test_dynamic_scoring_decay(app):
    """Verify linear and logarithmic decay dynamic calculations."""
    with app.app_context():
        # 1. Linear Decay Test
        ch_linear = ChallengeService.create_challenge(
            legacy_id="ch_linear",
            title="Linear Challenge",
            description="Desc",
            points=100,
            difficulty="Medium",
            decay_type="linear",
            decay_rate=15,
            minimum_points=40
        )
        # 0 solves -> 100 points
        assert ScoringService.calculate_points(ch_linear, 0) == 100
        # 1 solve -> 100 - 15 = 85
        assert ScoringService.calculate_points(ch_linear, 1) == 85
        # 5 solves -> 100 - (15*5) = 25 (clamped to min points = 40)
        assert ScoringService.calculate_points(ch_linear, 5) == 40

        # 2. Logarithmic Decay Test
        ch_log = ChallengeService.create_challenge(
            legacy_id="ch_log",
            title="Logarithmic Challenge",
            description="Desc",
            points=200,
            difficulty="Hard",
            decay_type="logarithmic",
            decay_rate=10, # threshold solves limit
            minimum_points=50
        )
        # 0 solves -> 200 points
        assert ScoringService.calculate_points(ch_log, 0) == 200
        # 1 solve -> 200 points
        assert ScoringService.calculate_points(ch_log, 1) == 200
        # 2 solves -> 200 - (200 - 50) * (log(2) / log(10)) = 200 - 150 * 0.301 = 154
        assert ScoringService.calculate_points(ch_log, 2) == 155
        # 10 solves -> 200 - (200 - 50) * (log(10) / log(10)) = 50 (decay target reached)
        assert ScoringService.calculate_points(ch_log, 10) == 50
        # 20 solves -> should clamp to minimum of 50
        assert ScoringService.calculate_points(ch_log, 20) == 50

def test_file_upload_sanitization_and_hashing(app, tmp_path):
    """Verify filename sanitization, hash generation, and file deletion."""
    with app.app_context():
        ch = ChallengeService.create_challenge("ch_file_test", "File Test", "Desc", 50, "Easy")
        
        # Mock file upload object using Werkzeug FileStorage
        from werkzeug.datastructures import FileStorage
        mock_file = FileStorage(
            stream=io.BytesIO(b"FLAG{file_content_flag}"),
            filename="../../danger/payload.txt"
        )
        
        upload_folder = str(tmp_path / "uploads")
        
        cf, err = FileService.upload_file(ch.id, mock_file, upload_folder)
        assert err is None
        assert cf is not None
        
        # Verify directory traversal was removed
        assert ".." not in cf.stored_filename
        assert "/" not in cf.stored_filename
        assert "\\" not in cf.stored_filename
        assert cf.original_filename == "../../danger/payload.txt"
        assert cf.size == len("FLAG{file_content_flag}")
        
        # Verify SHA-256 Checksum matches content
        expected_hash = hashlib.sha256(b"FLAG{file_content_flag}").hexdigest()
        assert cf.checksum == expected_hash

        # Track download count
        FileService.track_download(cf.id)
        assert cf.download_count == 1

        # Delete file
        success, _ = FileService.delete_file(cf.id, upload_folder)
        assert success is True
        
        # Verify file deleted from disk
        assert not os.path.exists(os.path.join(upload_folder, cf.stored_filename))
