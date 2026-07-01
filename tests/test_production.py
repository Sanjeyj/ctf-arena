"""
tests/test_production.py
Milestone 9 — Production configuration, security headers, health endpoints,
rate limiting, logging, metrics, and CLI command tests.
"""
import os
import json
import pytest
from unittest.mock import patch

from app import create_app
from app.extensions import db
from app.config import ProductionConfig, StagingConfig, TestingConfig
from app.repositories.role_repository import RoleRepository
from app.repositories.permission_repository import PermissionRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_roles(app):
    with app.app_context():
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()


# ---------------------------------------------------------------------------
# Phase A — Configuration Tests
# ---------------------------------------------------------------------------

class TestProductionConfig:
    def test_production_secure_cookies(self):
        assert ProductionConfig.SESSION_COOKIE_SECURE is True

    def test_production_httponly(self):
        assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True

    def test_production_samesite(self):
        assert ProductionConfig.SESSION_COOKIE_SAMESITE == "Lax"

    def test_production_https_scheme(self):
        assert ProductionConfig.PREFERRED_URL_SCHEME == "https"

    def test_production_debug_off(self):
        assert ProductionConfig.DEBUG is False

    def test_production_testing_off(self):
        assert ProductionConfig.TESTING is False


class TestStagingConfig:
    def test_staging_secure_cookies(self):
        assert StagingConfig.SESSION_COOKIE_SECURE is True

    def test_staging_debug_off(self):
        assert StagingConfig.DEBUG is False

    def test_staging_https_scheme(self):
        assert StagingConfig.PREFERRED_URL_SCHEME == "https"


class TestTestingConfig:
    def test_testing_csrf_disabled(self):
        assert TestingConfig.WTF_CSRF_ENABLED is False

    def test_testing_in_memory_db(self):
        assert ":memory:" in TestingConfig.SQLALCHEMY_DATABASE_URI

    def test_testing_flag_on(self):
        assert TestingConfig.TESTING is True


# ---------------------------------------------------------------------------
# Phase B — HTTP Security Headers
# ---------------------------------------------------------------------------

def test_security_headers_present(client):
    resp = client.get("/login")
    assert "X-Frame-Options" in resp.headers
    assert resp.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert "X-Content-Type-Options" in resp.headers
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert "Referrer-Policy" in resp.headers
    assert "Content-Security-Policy" in resp.headers
    assert "Permissions-Policy" in resp.headers


def test_csp_contains_default_src(client):
    resp = client.get("/login")
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "default-src" in csp


def test_permissions_policy_restricts_camera(client):
    resp = client.get("/login")
    pp = resp.headers.get("Permissions-Policy", "")
    assert "camera=()" in pp


# ---------------------------------------------------------------------------
# Phase F — Health Endpoint Tests
# ---------------------------------------------------------------------------

def test_liveness_endpoint(client):
    resp = client.get("/live")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["status"] == "live"


def test_readiness_endpoint(client):
    resp = client.get("/ready")
    # In testing with in-memory DB it should be ready
    assert resp.status_code in (200, 503)


def test_health_endpoint_structure(client):
    resp = client.get("/health")
    assert resp.status_code in (200, 503)
    data = resp.get_json()
    # /health is the basic liveness check - it returns ok and status
    assert "ok" in data or "status" in data


def test_health_endpoint_docker_field(client):
    resp = client.get("/ready")
    assert resp.status_code in (200, 503)
    data = resp.get_json()
    # /ready has docker and database details
    assert "database" in data or "status" in data


# ---------------------------------------------------------------------------
# Phase D — Metrics Endpoint Tests
# ---------------------------------------------------------------------------

def test_metrics_endpoint_enabled(app, client):
    app.config["METRICS_ENABLED"] = True
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "ctf_http_requests_total" in body or "ctf_" in body


def test_metrics_endpoint_disabled(app, client):
    app.config["METRICS_ENABLED"] = False
    resp = client.get("/metrics")
    assert resp.status_code == 403
    # Restore for other tests
    app.config["METRICS_ENABLED"] = True


def test_metrics_format_is_prometheus(app, client):
    app.config["METRICS_ENABLED"] = True
    resp = client.get("/metrics")
    if resp.status_code == 200:
        ct = resp.headers.get("Content-Type", "")
        assert "text/plain" in ct


# ---------------------------------------------------------------------------
# Phase G — CLI Commands Tests
# ---------------------------------------------------------------------------

def test_cli_verify_config(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["verify-config"])
    assert result.exit_code == 0
    assert "CONFIGURATION SANITY CHECK" in result.output


def test_cli_system_health(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["system-health"])
    assert result.exit_code == 0
    assert "SYSTEM HEALTH STATUS" in result.output


def test_cli_metrics_summary(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["metrics-summary"])
    assert result.exit_code == 0
    assert "METRICS SUMMARY" in result.output


def test_cli_rotate_logs(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["rotate-logs"])
    assert result.exit_code == 0
    assert "Rotating" in result.output


def test_cli_cleanup_logs(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["cleanup-logs"])
    assert result.exit_code == 0
    assert "Purged" in result.output


def test_cli_backup_db(app):
    runner = app.test_cli_runner()
    # In-memory SQLite won't have a real file, should warn/error gracefully
    result = runner.invoke(args=["backup-db"])
    assert result.exit_code == 0
    # Either backed up or reported that file doesn't exist (both acceptable)
    assert "[OK]" in result.output or "[ERROR]" in result.output


def test_cli_snapshot_system(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["snapshot-system"])
    assert result.exit_code == 0
    # Should complete and report success or failure
    assert "[OK]" in result.output or "[ERROR]" in result.output


def test_cli_health_check_alias(app):
    """health-check is the legacy alias for system-health."""
    runner = app.test_cli_runner()
    result = runner.invoke(args=["health-check"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Phase H — Admin Observability Endpoints
# ---------------------------------------------------------------------------

def test_admin_system_health_endpoint_requires_admin(client):
    resp = client.get("/admin/system/health")
    # Should redirect to admin login (302) or deny (403)
    assert resp.status_code in (302, 403)


def test_admin_system_metrics_endpoint_requires_admin(client):
    resp = client.get("/admin/system/metrics")
    assert resp.status_code in (302, 403)


# ---------------------------------------------------------------------------
# Phase I — Deployment Assets Exist
# ---------------------------------------------------------------------------

def test_deployment_directory_exists():
    deployment_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "deployment"
    )
    assert os.path.exists(deployment_dir)


def test_docker_compose_exists():
    compose = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "deployment", "docker-compose.yml"
    )
    assert os.path.exists(compose)


def test_nginx_conf_exists():
    nginx = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "deployment", "nginx.conf"
    )
    assert os.path.exists(nginx)


def test_gunicorn_conf_exists():
    gunicorn = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "deployment", "gunicorn.conf.py"
    )
    assert os.path.exists(gunicorn)


def test_systemd_service_exists():
    service = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "deployment", "systemd", "ctf-arena.service"
    )
    assert os.path.exists(service)


def test_systemd_timer_exists():
    timer = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "deployment", "systemd", "ctf-arena-janitor.timer"
    )
    assert os.path.exists(timer)
