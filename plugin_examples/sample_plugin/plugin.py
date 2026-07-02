# Standard Sample Plugin Template entry point
from flask import jsonify

def my_view():
    return jsonify({"message": "Hello from the Sandbox template!"})

def setup(api):
    api.register_route("/plugins/sandbox/demo", "sandbox_demo_route", my_view)
