import os
import json
import zipfile
import shutil
import importlib.util
import logging
from flask import current_app
from app.extensions import db, safe_commit
from app.models.plugin_installation import PluginInstallation
from app.models.plugin_permission import PluginPermission
from app.models.plugin_setting import PluginSetting
from app.services.plugin_security import PluginSecurity
from app.services.hook_service import HookService

logger = logging.getLogger(__name__)

class PluginAPI:
    def __init__(self, plugin_name, plugin_dir):
        self.plugin_name = plugin_name
        self.plugin_dir = plugin_dir

    def register_route(self, rule, endpoint, view_func, **options):
        """Register a custom page route dynamically on the Flask application."""
        current_app.add_url_rule(rule, endpoint, view_func, **options)
        logger.info(f"[PluginAPI] Registered page route '{rule}' for plugin '{self.plugin_name}'")

    def register_api(self, rule, endpoint, view_func, **options):
        """Register a custom JSON REST API route dynamically."""
        api_rule = f"/api/v1/plugins/{self.plugin_name.lower().replace(' ', '_')}{rule}"
        current_app.add_url_rule(api_rule, endpoint, view_func, **options)
        logger.info(f"[PluginAPI] Registered API route '{api_rule}' for plugin '{self.plugin_name}'")

    def register_menu(self, title, route):
        """Append navigation links to the user or admin menu."""
        PluginService.register_menu_item(title, route)

    def register_hook(self, hook_name, callback):
        """Register a lifecycle hook listener."""
        HookService.register_hook(hook_name, callback)

    def register_template(self, original, override):
        """Override core HTML template views dynamically."""
        PluginService.register_template_override(original, override)


class PluginService:
    _menu_items = []  # List of {"title": title, "route": route}
    _template_overrides = {}  # original_template_path -> override_template_path
    _loaded_modules = {} # plugin_name -> module instance

    @classmethod
    def get_menu_items(cls):
        return cls._menu_items

    @classmethod
    def register_menu_item(cls, title, route):
        cls._menu_items.append({"title": title, "route": route})

    @classmethod
    def get_template_override(cls, original):
        return cls._template_overrides.get(original, original)

    @classmethod
    def register_template_override(cls, original, override):
        cls._template_overrides[original] = override

    @staticmethod
    def get_plugins_dir():
        plugins_dir = os.path.join(current_app.root_path, "..", "plugins")
        os.makedirs(plugins_dir, exist_ok=True)
        return os.path.abspath(plugins_dir)

    @staticmethod
    def discover_plugins():
        """Scans the plugins/ directory for plugin manifests (plugin.json).
        
        Returns:
            List of dicts containing plugin manifest properties and DB status.
        """
        plugins_dir = PluginService.get_plugins_dir()
        discovered = []

        if not os.path.exists(plugins_dir):
            return discovered

        for folder in os.listdir(plugins_dir):
            folder_path = os.path.join(plugins_dir, folder)
            if not os.path.isdir(folder_path):
                continue

            manifest_path = os.path.join(folder_path, "plugin.json")
            if not os.path.exists(manifest_path):
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                
                # Check database status
                db_inst = PluginInstallation.query.filter_by(plugin_name=manifest["name"]).first()
                manifest["enabled"] = db_inst.enabled if db_inst else False
                manifest["installed"] = db_inst is not None
                manifest["folder_name"] = folder
                
                discovered.append(manifest)
            except Exception as e:
                logger.error(f"[PluginService] Failed reading manifest for {folder}: {str(e)}")

        return discovered

    @staticmethod
    def load_plugin(plugin_name):
        """Loads and executes a plugin's entry point if enabled and passes security scanner checks."""
        if plugin_name in PluginService._loaded_modules:
            return True

        plugins_dir = PluginService.get_plugins_dir()
        manifest = None

        # Find plugin folder by scanning manifests
        for folder in os.listdir(plugins_dir):
            folder_path = os.path.join(plugins_dir, folder)
            manifest_path = os.path.join(folder_path, "plugin.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data["name"] == plugin_name:
                        manifest = data
                        manifest["folder"] = folder_path
                        break
                except:
                    continue

        if not manifest:
            logger.error(f"[PluginService] Plugin '{plugin_name}' manifest not found.")
            return False

        # Run security check
        status, reasons = PluginSecurity.scan_plugin(manifest["folder"])
        if status == "BLOCKED":
            logger.error(f"[PluginService] Blocked loading plugin '{plugin_name}' due to security violations: {reasons}")
            return False

        # Load entry python file
        entry_file = manifest.get("entry", "plugin.py")
        entry_path = os.path.join(manifest["folder"], entry_file)
        if not os.path.exists(entry_path):
            logger.error(f"[PluginService] Entry file '{entry_file}' not found for '{plugin_name}'")
            return False

        try:
            # Dynamic python import
            spec = importlib.util.spec_from_file_location(plugin_name, entry_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Invoke setup handler passing PluginAPI helper
            api = PluginAPI(plugin_name, manifest["folder"])
            if hasattr(module, "setup"):
                module.setup(api)

            PluginService._loaded_modules[plugin_name] = module
            logger.info(f"[PluginService] Successfully loaded plugin '{plugin_name}' version {manifest['version']}")
            return True
        except Exception as e:
            logger.error(f"[PluginService] Failed loading module for '{plugin_name}': {str(e)}", exc_info=True)
            return False

    @staticmethod
    def load_enabled_plugins():
        """Bootstraps and loads all plugins marked enabled in the database."""
        enabled_installations = PluginInstallation.query.filter_by(enabled=True).all()
        for inst in enabled_installations:
            PluginService.load_plugin(inst.plugin_name)

    @staticmethod
    def enable_plugin(plugin_name):
        """Marks a plugin enabled in the DB and triggers execution loading."""
        db_inst = PluginInstallation.query.filter_by(plugin_name=plugin_name).first()
        if not db_inst:
            # Try to discover it to seed entry
            discovered = PluginService.discover_plugins()
            manifest = next((p for p in discovered if p["name"] == plugin_name), None)
            if not manifest:
                return False
            
            db_inst = PluginInstallation(
                plugin_name=manifest["name"],
                version=manifest["version"],
                author=manifest.get("author", "Unknown"),
                enabled=True
            )
            db.session.add(db_inst)
            # Add requested permissions
            for perm in manifest.get("permissions", []):
                db_perm = PluginPermission(plugin=db_inst, permission_name=perm, granted=True)
                db.session.add(db_perm)
        else:
            db_inst.enabled = True
        
        safe_commit()
        # Trigger load
        return PluginService.load_plugin(plugin_name)

    @staticmethod
    def disable_plugin(plugin_name):
        """Disables a plugin in the database."""
        db_inst = PluginInstallation.query.filter_by(plugin_name=plugin_name).first()
        if db_inst:
            db_inst.enabled = False
            safe_commit()
            
            # Note: Python does not easily support hot-unloading modules at runtime.
            # We remove it from loaded references and clear any hook callbacks it registered.
            if plugin_name in PluginService._loaded_modules:
                del PluginService._loaded_modules[plugin_name]
            logger.info(f"[PluginService] Disabled plugin '{plugin_name}'")
            return True
        return False

    @staticmethod
    def uninstall_plugin(plugin_name):
        """Disables, deletes DB configuration metadata, and purges plugin files."""
        PluginService.disable_plugin(plugin_name)
        
        db_inst = PluginInstallation.query.filter_by(plugin_name=plugin_name).first()
        if db_inst:
            db.session.delete(db_inst)
            safe_commit()

        # Purge from disk folder
        plugins_dir = PluginService.get_plugins_dir()
        for folder in os.listdir(plugins_dir):
            folder_path = os.path.join(plugins_dir, folder)
            manifest_path = os.path.join(folder_path, "plugin.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data["name"] == plugin_name:
                        shutil.rmtree(folder_path)
                        logger.info(f"[PluginService] Purged folder {folder_path} from disk.")
                        break
                except:
                    continue
        return True

    @staticmethod
    def install_plugin_zip(zip_path):
        """Extracts a plugin ZIP package to the plugins directory and scans manifest."""
        if not zipfile.is_zipfile(zip_path):
            raise ValueError("File is not a valid zip archive")

        plugins_dir = PluginService.get_plugins_dir()
        temp_extract = os.path.join(plugins_dir, "_temp_extract")
        os.makedirs(temp_extract, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract)

            # Locate manifest in extracted files
            manifest_file = None
            extracted_folder = temp_extract
            
            # Handle double nesting in ZIP files
            for root, dirs, files in os.walk(temp_extract):
                if "plugin.json" in files:
                    manifest_file = os.path.join(root, "plugin.json")
                    extracted_folder = root
                    break

            if not manifest_file:
                raise ValueError("ZIP archive is missing 'plugin.json' manifest file")

            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            plugin_name = manifest.get("name")
            if not plugin_name:
                raise ValueError("Manifest is missing 'name' field")

            # Final destination folder basename
            dest_folder = os.path.join(plugins_dir, plugin_name.lower().replace(" ", "_"))
            if os.path.exists(dest_folder):
                shutil.rmtree(dest_folder)

            shutil.copytree(extracted_folder, dest_folder)
            logger.info(f"[PluginService] Installed plugin '{plugin_name}' to {dest_folder}")
            return manifest
            
        finally:
            if os.path.exists(temp_extract):
                shutil.rmtree(temp_extract)
