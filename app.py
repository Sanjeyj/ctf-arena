from flask import Flask, render_template, request, redirect, make_response, jsonify, send_from_directory, session
import json, os, datetime

app = Flask(__name__)
app.secret_key = "ctf_super_secret_2024"

CHALLENGES = {
    "ch1": {
        "id": "ch1", "num": 1,
        "title": "Caesar's Secret",
        "category": "Cryptography",
        "points": 50,
        "icon": "🔐",
        "difficulty": "Easy",
        "description": "Julius left you a message. Can you decode it?",
        "flag": "FLAG{caesar_salad_is_delicious}"
    },
    "ch2": {
        "id": "ch2", "num": 2,
        "title": "Cookie Monster",
        "category": "Web Exploitation",
        "points": 75,
        "icon": "🍪",
        "difficulty": "Easy",
        "description": "Only admins are allowed. You don't have credentials — but maybe you don't need them.",
        "flag": "FLAG{c00ki3s_are_delic10us}"
    },
    "ch3": {
        "id": "ch3", "num": 3,
        "title": "Hidden in Plain Sight",
        "category": "Steganography",
        "points": 75,
        "icon": "🖼️",
        "difficulty": "Easy",
        "description": "Here's a cute cat image. Or is it just a cat? Download it and investigate.",
        "flag": "FLAG{steg0_master_101}"
    },
    "ch4": {
        "id": "ch4", "num": 4,
        "title": "Base Jumping",
        "category": "Encoding",
        "points": 50,
        "icon": "💻",
        "difficulty": "Easy",
        "description": "Sometimes secrets are just hiding in plain encoding.",
        "flag": "FLAG{base64_is_not_encryption}"
    },
    "ch5": {
        "id": "ch5", "num": 5,
        "title": "GitLeaks",
        "category": "OSINT",
        "points": 100,
        "icon": "🔎",
        "difficulty": "Easy",
        "description": "A developer accidentally committed something they shouldn't have. Dig through the commit history.",
        "flag": "FLAG{git_gud_at_osint}"
    },
}

SOLVED_FILE = "solved.json"

def get_solved():
    if os.path.exists(SOLVED_FILE):
        with open(SOLVED_FILE) as f:
            return json.load(f)
    return {}

def save_solved(data):
    with open(SOLVED_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
def index():
    solved = get_solved()
    total_pts = sum(CHALLENGES[c]["points"] for c in solved if c in CHALLENGES)
    return render_template("index.html", challenges=CHALLENGES, solved=solved, total_pts=total_pts)

@app.route("/challenge/<ch_id>")
def challenge(ch_id):
    ch = CHALLENGES.get(ch_id)
    if not ch:
        return redirect("/")
    solved = get_solved()
    return render_template(f"ch_{ch_id}.html", ch=ch, solved=solved)

@app.route("/submit/<ch_id>", methods=["POST"])
def submit(ch_id):
    ch = CHALLENGES.get(ch_id)
    if not ch:
        return jsonify({"success": False, "msg": "Challenge not found"})
    flag = request.form.get("flag", "").strip()
    solved = get_solved()
    if ch_id in solved:
        return jsonify({"success": True, "msg": "Already solved! 🎉", "points": ch["points"]})
    if flag == ch["flag"]:
        solved[ch_id] = {"time": datetime.datetime.now().isoformat(), "points": ch["points"]}
        save_solved(solved)
        return jsonify({"success": True, "msg": f"Correct! +{ch['points']} points 🎉", "points": ch["points"]})
    return jsonify({"success": False, "msg": "Wrong flag. Try again! ❌"})

@app.route("/cookie-check")
def cookie_check():
    role = request.cookies.get("role", "guest")
    if role == "admin":
        return jsonify({"status": "Welcome admin!", "flag": "FLAG{c00ki3s_are_delic10us}"})
    resp = make_response(jsonify({"status": f"Access denied. You are: {role}", "hint": "Only admins can see the flag..."}))
    resp.set_cookie("role", "guest")
    return resp

@app.route("/static/files/<filename>")
def serve_file(filename):
    return send_from_directory("static/files", filename)

@app.route("/reset")
def reset():
    if os.path.exists(SOLVED_FILE):
        os.remove(SOLVED_FILE)
    return redirect("/")

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  🚩 CTF Challenge Server - Easy Level")
    print("  Running at: http://localhost:5000")
    print("="*55 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
