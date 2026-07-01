import sys
import os
import inspect
from flask import Flask

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app

def audit_routes(app):
    print("\n--- Route Auditing ---")
    routes = {}
    duplicates = []
    
    for rule in app.url_map.iter_rules():
        route_str = f"{rule.methods} {rule.rule}"
        endpoint = rule.endpoint
        
        if rule.rule in routes:
            # Check if there is overlap in methods
            existing_methods, existing_endpoint = routes[rule.rule]
            overlap = rule.methods.intersection(existing_methods)
            if overlap:
                duplicates.append(f"Rule: {rule.rule}, Methods: {overlap}, Endpoints: {endpoint} vs {existing_endpoint}")
        else:
            routes[rule.rule] = (rule.methods, endpoint)
            
        print(f"Endpoint: {endpoint:<30} Route: {rule.rule:<40} Methods: {list(rule.methods)}")
        
    if duplicates:
        print("\n[FAIL] Duplicate routes found:")
        for dup in duplicates:
            print(f" - {dup}")
        return False
    else:
        print("\n[OK] No duplicate routes found.")
        return True

def audit_blueprints(app):
    print("\n--- Blueprint Registration Auditing ---")
    registered_blueprints = list(app.blueprints.keys())
    print(f"Registered Blueprints ({len(registered_blueprints)}): {registered_blueprints}")
    
    # We registered 22 blueprints (5 core + 17 skeletons)
    expected_blueprints = 22
    if len(registered_blueprints) == expected_blueprints:
        print(f"[OK] Blueprint count matches expected ({expected_blueprints}).")
        return True
    else:
        print(f"[WARN] Blueprint count is {len(registered_blueprints)}, expected {expected_blueprints}.")
        return False

def audit_circular_imports():
    print("\n--- Circular Import Auditing ---")
    try:
        from app.auth import routes as auth_r
        from app.challenges import routes as chal_r
        from app.admin import routes as admin_r
        from app.scoreboard import routes as score_r
        from app.api import routes as api_r
        print("[OK] Core blueprint routes imported successfully without circular dependency loops.")
        return True
    except Exception as e:
        print(f"[FAIL] Circular import or module load error: {e}")
        return False

def audit_cli_commands(app):
    print("\n--- CLI Command Auditing ---")
    commands = list(app.cli.commands.keys())
    print(f"Registered CLI Commands: {commands}")
    expected_cmds = ["init-db", "seed", "backup", "restore", "create-admin", "import", "export", "health-check"]
    
    missing = [cmd for cmd in expected_cmds if cmd not in commands]
    if not missing:
        print("[OK] All required CLI commands are registered successfully.")
        return True
    else:
        print(f"[FAIL] Missing CLI commands: {missing}")
        return False

def audit_logging(app):
    print("\n--- Logging Initialization Auditing ---")
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
    log_files = ["app.log", "error.log", "access.log"]
    all_exist = True
    
    for log_file in log_files:
        path = os.path.join(log_dir, log_file)
        if os.path.exists(path):
            print(f"[OK] Log file exists: {log_file}")
        else:
            print(f"[WARN] Log file missing (will generate on write): {log_file}")
            all_exist = False
            
    # Check if handlers are registered on app logger
    if len(app.logger.handlers) >= 2:
        print("[OK] Logging handlers registered successfully on Flask app.")
        return True
    else:
        print("[FAIL] Missing log handlers.")
        return False

def main():
    print("==================================================")
    print("         CTF Arena v2 Project Health Audit        ")
    print("==================================================")
    
    # Initialize application
    app = create_app("testing")
    
    route_ok = audit_routes(app)
    bp_ok = audit_blueprints(app)
    imports_ok = audit_circular_imports()
    cli_ok = audit_cli_commands(app)
    logging_ok = audit_logging(app)
    
    all_ok = route_ok and bp_ok and imports_ok and cli_ok and logging_ok
    
    print("\n==================================================")
    if all_ok:
        print("          AUDIT STATUS: ALL PASSED (100%)         ")
        sys.exit(0)
    else:
        print("          AUDIT STATUS: FAIL / WARN PRESENT       ")
        sys.exit(1)

if __name__ == "__main__":
    main()
