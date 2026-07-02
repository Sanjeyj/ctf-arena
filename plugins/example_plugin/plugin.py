# Example Plugin entry point
from flask import jsonify

def custom_page_view():
    return jsonify({
        "status": "success",
        "message": "Hello from Example Plugin custom page route!"
    })

def custom_api_view():
    return jsonify({
        "status": "success",
        "message": "Hello from Example Plugin REST API!"
    })

# Hook callbacks
def on_user_login(user, ip_address):
    print(f"[ExamplePlugin] Hook triggered! User '{user.username}' logged in from {ip_address}")

def on_score_update(challenge, solve_count):
    # Demonstrate custom scoring override (always award 1337 points if challenge legacy_id is 'ch_extreme')
    if challenge.legacy_id == "ch_extreme":
        return 1337
    return None

def setup(api):
    """Entry point handler invoked by the CTF Arena Plugin Engine."""
    # 1. Register page route
    api.register_route("/plugins/example/test", "example_plugin_test_route", custom_page_view, methods=["GET"])

    # 2. Register API endpoint
    api.register_api("/hello", "example_plugin_api_hello", custom_api_view, methods=["GET"])

    # 3. Register hooks listeners
    api.register_hook("after_login", on_user_login)
    api.register_hook("before_score_update", on_score_update)
