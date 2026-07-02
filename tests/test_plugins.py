import os
import json
import zipfile
import tempfile
import pytest
from app.extensions import db
from app.models.plugin_installation import PluginInstallation
from app.models.plugin_permission import PluginPermission
from app.models.plugin_setting import PluginSetting
from app.services.plugin_service import PluginService
from app.services.plugin_security import PluginSecurity
from app.services.hook_service import HookService
from app.models.challenge import Challenge
from app.models.category import Category
from app.services.scoring_service import ScoringService

@pytest.fixture(autouse=True)
def clean_hooks():
    HookService.clear_all()
    PluginService._loaded_modules.clear()
    PluginService._menu_items.clear()
    PluginService._template_overrides.clear()
    yield
    HookService.clear_all()
    PluginService._loaded_modules.clear()
    PluginService._menu_items.clear()
    PluginService._template_overrides.clear()

def test_plugin_discovery_and_db_models(app):
    """Test 1: Verify discovered plugins match installed files and check DB model bindings."""
    with app.app_context():
        # Setup DB entries
        inst = PluginInstallation(plugin_name="Example Plugin", version="1.0.0", enabled=True)
        db.session.add(inst)
        db.session.flush()
        
        perm = PluginPermission(plugin_installation_id=inst.id, permission_name="NETWORK_ACCESS", granted=True)
        setting = PluginSetting(plugin_installation_id=inst.id, key="webhook_url", value="https://discord.com")
        db.session.add_all([perm, setting])
        db.session.commit()

        # Discover
        plugins = PluginService.discover_plugins()
        example = next((p for p in plugins if p["name"] == "Example Plugin"), None)
        
        assert example is not None
        assert example["installed"] is True
        assert example["enabled"] is True

        # Query relation records
        queried_inst = PluginInstallation.query.filter_by(plugin_name="Example Plugin").first()
        assert len(queried_inst.permissions) == 1
        assert len(queried_inst.settings) == 1
        assert queried_inst.permissions[0].permission_name == "NETWORK_ACCESS"

def test_plugin_enable_disable_lifecycle(app):
    """Test 2: Verify enable, disable, and reload lifecycle flows."""
    with app.app_context():
        # Make sure it starts clean
        inst = PluginInstallation.query.filter_by(plugin_name="Example Plugin").first()
        if inst:
            db.session.delete(inst)
            db.session.commit()

        # Enable
        ok = PluginService.enable_plugin("Example Plugin")
        assert ok is True
        
        db_inst = PluginInstallation.query.filter_by(plugin_name="Example Plugin").first()
        assert db_inst is not None
        assert db_inst.enabled is True

        # Disable
        ok_disable = PluginService.disable_plugin("Example Plugin")
        assert ok_disable is True
        assert db_inst.enabled is False

def test_plugin_hook_execution(app):
    """Test 3: Verify registering, triggering, and removing hooks."""
    called = []
    def callback(user_val):
        called.append(user_val)

    HookService.register_hook("test_event", callback)
    HookService.trigger_hook("test_event", "hello_world")
    
    assert len(called) == 1
    assert called[0] == "hello_world"

    HookService.remove_hook("test_event", callback)
    HookService.trigger_hook("test_event", "second_call")
    # Should not append anything since callback is removed
    assert len(called) == 1

def test_plugin_ast_security_scanner(app):
    """Test 4: Verify security scanner blocks dangerous commands and allows safe files."""
    # Write temporary python files to evaluate
    with tempfile.TemporaryDirectory() as tmpdir:
        # Safe python code
        with open(os.path.join(tmpdir, "safe.py"), "w") as f:
            f.write("def run():\n    print('Hello')\n")
        
        # Unsafe python code (importing subprocess)
        with open(os.path.join(tmpdir, "unsafe_import.py"), "w") as f:
            f.write("import subprocess\n")

        # Unsafe python code (calling eval)
        with open(os.path.join(tmpdir, "unsafe_call.py"), "w") as f:
            f.write("eval('1+1')\n")

        # Run scanner
        status_safe, _ = PluginSecurity.scan_plugin(tmpdir)
        # Note: scanner walks whole directory, if any unsafe file is found, it blocks
        
    # Test safe folder
    with tempfile.TemporaryDirectory() as tmpdir_safe:
        with open(os.path.join(tmpdir_safe, "plugin.py"), "w") as f:
            f.write("def setup():\n    pass\n")
        status, _ = PluginSecurity.scan_plugin(tmpdir_safe)
        assert status == "SAFE"

    # Test unsafe folder
    with tempfile.TemporaryDirectory() as tmpdir_unsafe:
        with open(os.path.join(tmpdir_unsafe, "plugin.py"), "w") as f:
            f.write("import subprocess\n")
        status, reasons = PluginSecurity.scan_plugin(tmpdir_unsafe)
        assert status == "BLOCKED"
        assert any("Restricted module import" in r for r in reasons)

def test_plugin_route_registration(app):
    """Test 5: Verify route registration is hooked dynamically on Flask app context."""
    with app.test_client() as client:
        # Load Example Plugin to register /plugins/example/test route
        with app.app_context():
            PluginService.load_plugin("Example Plugin")

        # Request custom registered route page
        resp = client.get("/plugins/example/test")
        assert resp.status_code == 200
        json_data = resp.get_json()
        assert json_data["status"] == "success"
        assert "Hello from Example Plugin" in json_data["message"]

def test_plugin_zip_installation(app):
    """Test 6: Test installing a plugin packaged in a ZIP archive."""
    with app.app_context():
        # Build in-memory zip
        zip_fd, zip_path = tempfile.mkstemp(suffix=".zip")
        try:
            with zipfile.ZipFile(zip_path, "w") as z:
                # Add plugin.json
                manifest = {
                    "name": "Zip Plugin",
                    "version": "1.2.3",
                    "author": "Tester",
                    "entry": "plugin.py"
                }
                z.writestr("plugin.json", json.dumps(manifest))
                z.writestr("plugin.py", "def setup(api):\n    pass\n")

            # Run installation
            installed_manifest = PluginService.install_plugin_zip(zip_path)
            assert installed_manifest["name"] == "Zip Plugin"
            assert installed_manifest["version"] == "1.2.3"
            
            # Clean up files from disk
            PluginService.uninstall_plugin("Zip Plugin")
            
        finally:
            os.close(zip_fd)
            if os.path.exists(zip_path):
                os.remove(zip_path)

def test_scoring_hook_override(app):
    """Test 7: Verify before_score_update hook allows custom scoring overrides."""
    with app.app_context():
        # Setup challenge
        cat = Category(name="web_scoring")
        db.session.add(cat)
        db.session.flush()

        ch_normal = Challenge(
            legacy_id="ch_normal",
            title="ChNormal",
            description="desc",
            points=100,
            initial_points=100,
            minimum_points=10,
            difficulty="Easy",
            category_id=cat.id
        )
        ch_extreme = Challenge(
            legacy_id="ch_extreme",
            title="ChExtreme",
            description="desc",
            points=500,
            initial_points=500,
            minimum_points=50,
            difficulty="Hard",
            category_id=cat.id
        )
        db.session.add_all([ch_normal, ch_extreme])
        db.session.commit()

        # Score normally
        score_normal = ScoringService.calculate_points(ch_normal)
        score_extreme = ScoringService.calculate_points(ch_extreme)
        assert score_normal == 100
        assert score_extreme == 500

        # Enable Example Plugin (which overrides ch_extreme to 1337 points)
        ok = PluginService.load_plugin("Example Plugin")
        assert ok is True

        # Recalculate scores
        override_normal = ScoringService.calculate_points(ch_normal)
        override_extreme = ScoringService.calculate_points(ch_extreme)
        
        # ch_normal should remain unaffected (100)
        assert override_normal == 100
        # ch_extreme should be overridden to 1337
        assert override_extreme == 1337

def test_invalid_zip_upload_error(app):
    """Test 8: Ensure install_plugin_zip raises ValueError on non-zip uploads."""
    with app.app_context():
        fd, file_path = tempfile.mkstemp(suffix=".txt")
        try:
            with open(file_path, "w") as f:
                f.write("Not a zip file")
            with pytest.raises(ValueError, match="File is not a valid zip archive"):
                PluginService.install_plugin_zip(file_path)
        finally:
            os.close(fd)
            if os.path.exists(file_path):
                os.remove(file_path)

def test_missing_manifest_zip_error(app):
    """Test 9: Ensure install_plugin_zip raises ValueError if plugin.json is missing."""
    with app.app_context():
        zip_fd, zip_path = tempfile.mkstemp(suffix=".zip")
        try:
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("readme.txt", "No manifest here")
            with pytest.raises(ValueError, match="ZIP archive is missing 'plugin.json'"):
                PluginService.install_plugin_zip(zip_path)
        finally:
            os.close(zip_fd)
            if os.path.exists(zip_path):
                os.remove(zip_path)

def test_before_container_start_hook_trigger(app):
    """Test 10: Verify the before_container_start hook is called with correct parameters."""
    called = []
    def hook_fn(image_ref, container_name):
        called.append((image_ref, container_name))

    HookService.register_hook("before_container_start", hook_fn)
    
    from app.services.docker_service import DockerService
    DockerService.run_container("fake-image:latest", container_name="test_cnt")
    
    assert len(called) == 1
    assert called[0] == ("fake-image:latest", "test_cnt")

def test_after_container_stop_hook_trigger(app):
    """Test 11: Verify the after_container_stop hook is called with correct parameters."""
    called = []
    def hook_fn(container_id):
        called.append(container_id)

    HookService.register_hook("after_container_stop", hook_fn)
    
    from app.services.docker_service import DockerService
    DockerService.stop_container("fake_cid")
    
    assert len(called) == 1
    assert called[0] == "fake_cid"
