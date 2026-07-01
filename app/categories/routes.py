from flask import jsonify
from app.categories import categories_bp

@categories_bp.route("/api/v2/categories/placeholder")
def placeholder():
    return jsonify({"blueprint": "categories"})
