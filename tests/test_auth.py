import pytest
from flask import url_for
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService, hash_password
from app.services.permission_service import PermissionService

@pytest.fixture(autouse=True)
def setup_roles_and_perms(app):
    with app.app_context():
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

def test_user_registration(app):
    """Verify registration succeeds with correct values and fails with weak/mismatched values."""
    with app.app_context():
        # Valid registration
        user, err = AuthService.register_user(
            username="player1",
            password="Password123!",
            confirm_password="Password123!",
            display_name="Player One",
            email="player1@test.ctf"
        )
        assert err is None
        assert user is not None
        assert user.username == "player1"
        assert user.display_name == "Player One"
        assert user.email == "player1@test.ctf"
        assert user.role == "Participant"

        # Mismatched passwords
        _, err = AuthService.register_user("player2", "Password123!", "WrongPassword!", "P2")
        assert err == "Passwords do not match."

        # Weak password
        _, err = AuthService.register_user("player3", "weak", "weak", "P3")
        assert "at least 8 characters" in err or "uppercase" in err

        # Duplicate username
        _, err = AuthService.register_user("player1", "Password123!", "Password123!", "Player Dup")
        assert "already taken" in err

def test_authentication_and_lockout(app):
    """Verify login validation, login logging, and accounts lockout features."""
    with app.app_context():
        # Register a sample user
        user, _ = AuthService.register_user(
            username="lockout_user",
            password="Password123!",
            confirm_password="Password123!",
            display_name="Lockout Target"
        )
        
        # Test wrong login credentials
        res_user, err = AuthService.authenticate_user("lockout_user", "WrongPassword!")
        assert res_user is None
        assert err == "Invalid credentials."
        assert user.failed_login_attempts == 1

        # Test correct login
        res_user, err = AuthService.authenticate_user("lockout_user", "Password123!")
        assert res_user is not None
        assert err is None
        assert res_user.failed_login_attempts == 0

        # Trigger lockout (5 failures)
        for i in range(5):
            AuthService.authenticate_user("lockout_user", "WrongPassword!")
            
        assert user.failed_login_attempts >= 5
        
        # Subsequent correct attempts should be blocked
        res_user, err = AuthService.authenticate_user("lockout_user", "Password123!")
        assert res_user is None
        assert "locked" in err

def test_rbac_access_restrictions(app, client):
    """Verify role checks restrict non-admins and allow authorized admins."""
    # 1. Create a Participant
    with app.app_context():
        AuthService.register_user("regular_user", "Password123!", "Password123!")
    
    # Authenticate as participant
    client.post("/login", data={"username": "regular_user", "password": "Password123!"})
    
    # Access dashboard - should redirect to admin login or return 403
    resp = client.get("/admin", follow_redirects=True)
    assert b"Admin <span>Portal</span>" in resp.data # Redirected back to admin login because it lacks privileges

    # 2. Create an Admin
    with app.app_context():
        UserRepository.create(
            username="site_admin",
            password_hash=hash_password("AdminPass123!"),
            display_name="System Admin",
            role_name="Admin"
        )
    
    # Authenticate as admin
    client.post("/admin/login", data={"username": "site_admin", "password": "AdminPass123!"})
    
    # Access dashboard - should succeed
    resp = client.get("/admin")
    assert resp.status_code == 200
    assert b"Leaderboard" in resp.data or b"Admin" in resp.data

def test_csrf_protection_enforcement(app, client):
    """Verify that POST requests fail without a CSRF token when CSRF is active."""
    app.config["WTF_CSRF_ENABLED"] = True # Enable CSRF for this test specifically
    
    # POST without CSRF token
    resp = client.post("/submit/ch1", data={"flag": "FLAG{test}"})
    assert resp.status_code == 400
    assert b"CSRF" in resp.data
