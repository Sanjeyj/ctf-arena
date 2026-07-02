# Certificate Generator Plugin
from flask import jsonify

def download_certificate(username):
    return jsonify({
        "status": "success",
        "certificate_url": f"/static/certs/{username}_completion.pdf",
        "message": f"Successfully generated CTF completion certificate for user '{username}'!"
    })

def setup(api):
    # Register certificate download route
    api.register_route("/plugins/certificate/download/<username>", "download_user_certificate", download_certificate, methods=["GET"])
