from flask import (
    Flask, render_template, request, redirect,
    make_response, jsonify, send_from_directory, session, url_for
)
import json, os, datetime, sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ctf_super_secret_2024")

# ---------------------------------------------------------------------------
# Admin credentials (override via env vars in production)
# ---------------------------------------------------------------------------
ADMIN_USER     = os.environ.get("ADMIN_USER",     "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ctf_admin_2024")

# ---------------------------------------------------------------------------
# Challenge definitions
# ---------------------------------------------------------------------------
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
    "ch6": {
        "id": "ch6", "num": 6,
        "title": "Broken Vault",
        "category": "Web Exploitation",
        "points": 200,
        "icon": "🗄️",
        "difficulty": "Hard",
        "description": "An insecure document search vault is online at `/vault-search`. Find the hidden flag inside the vault by abusing the query logic.",
        "flag": "FLAG{sqli_is_still_alive_and_kicking}"
    },
    "ch7": {
        "id": "ch7", "num": 7,
        "title": "Whisper Protocol",
        "category": "Cryptography",
        "points": 200,
        "icon": "📡",
        "difficulty": "Hard",
        "description": "A secret transmission was intercepted. It is hex-encoded and encrypted with a repeating 3-character uppercase XOR key. Decrypt it to find the flag.",
        "flag": "FLAG{xor_ciphers_are_simple_but_effective}"
    },
}

SCORES_FILE = "scores.json"

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE) as f:
            return json.load(f)
    return {"participants": {}}


def save_scores(data):
    with open(SCORES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_participant_solved(username):
    """Return the solved dict for a specific participant."""
    data = load_scores()
    return data["participants"].get(username, {}).get("solved", {})


def compute_leaderboard(data):
    """Return sorted leaderboard list from scores data."""
    board = []
    for name, info in data["participants"].items():
        solved = info.get("solved", {})
        total_pts = sum(v["points"] for v in solved.values())
        solve_count = len(solved)
        # Last solve time for tie-breaking
        times = [v["time"] for v in solved.values()]
        last_solve = max(times) if times else info.get("registered_at", "")
        board.append({
            "name": name,
            "score": total_pts,
            "solve_count": solve_count,
            "solved": solved,
            "registered_at": info.get("registered_at", ""),
            "last_solve": last_solve,
        })
    # Sort: highest score first, then earliest last_solve for ties
    board.sort(key=lambda x: (-x["score"], x["last_solve"]))
    for i, entry in enumerate(board):
        entry["rank"] = i + 1
    return board


def build_stats(data):
    """Compute high-level stats for the admin dashboard."""
    participants = data["participants"]
    total_participants = len(participants)
    total_solves = sum(len(p["solved"]) for p in participants.values())

    # Solve count per challenge
    ch_solve_counts = {ch_id: 0 for ch_id in CHALLENGES}
    for p in participants.values():
        for ch_id in p.get("solved", {}):
            if ch_id in ch_solve_counts:
                ch_solve_counts[ch_id] += 1

    most_popular = max(ch_solve_counts, key=ch_solve_counts.get) if ch_solve_counts else None
    max_possible = sum(c["points"] for c in CHALLENGES.values())

    return {
        "total_participants": total_participants,
        "total_solves": total_solves,
        "ch_solve_counts": ch_solve_counts,
        "most_popular_ch": CHALLENGES[most_popular]["title"] if most_popular else "—",
        "max_possible": max_possible,
    }

# ---------------------------------------------------------------------------
# Auth guards
# ---------------------------------------------------------------------------

def require_login():
    """Redirect to /register if participant not logged in."""
    if "user" not in session:
        return redirect(url_for("register"))
    return None


def require_admin():
    """Return 403 if admin not logged in."""
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    return None

# ---------------------------------------------------------------------------
# Participant routes
# ---------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            error = "Please enter a display name."
        elif len(name) > 32:
            error = "Name must be 32 characters or fewer."
        elif name.lower() == "admin":
            error = "That name is reserved."
        else:
            data = load_scores()
            if name not in data["participants"]:
                data["participants"][name] = {
                    "registered_at": datetime.datetime.now().isoformat(),
                    "solved": {}
                }
                save_scores(data)
            session["user"] = name
            return redirect(url_for("index"))

    return render_template("register.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("register"))


@app.route("/")
def index():
    guard = require_login()
    if guard:
        return guard
    username = session["user"]
    solved = get_participant_solved(username)
    total_pts = sum(solved[c]["points"] for c in solved if c in CHALLENGES)
    
    data = load_scores()
    registered_at = data["participants"][username]["registered_at"]
    
    return render_template(
        "index.html",
        challenges=CHALLENGES,
        solved=solved,
        total_pts=total_pts,
        username=username,
        registered_at=registered_at
    )


@app.route("/challenge/<ch_id>")
def challenge(ch_id):
    guard = require_login()
    if guard:
        return guard
    ch = CHALLENGES.get(ch_id)
    if not ch:
        return redirect(url_for("index"))
    username = session["user"]
    solved = get_participant_solved(username)
    return render_template(f"ch_{ch_id}.html", ch=ch, solved=solved, username=username, challenges=CHALLENGES)


@app.route("/submit/<ch_id>", methods=["POST"])
def submit(ch_id):
    guard = require_login()
    if guard:
        return jsonify({"success": False, "msg": "Not logged in."})

    ch = CHALLENGES.get(ch_id)
    if not ch:
        return jsonify({"success": False, "msg": "Challenge not found."})

    username = session["user"]
    flag = request.form.get("flag", "").strip()

    data = load_scores()
    participant = data["participants"].setdefault(username, {
        "registered_at": datetime.datetime.now().isoformat(),
        "solved": {}
    })
    solved = participant.setdefault("solved", {})

    if ch_id in solved:
        return jsonify({"success": True, "msg": "Already solved! 🎉", "points": solved[ch_id]["points"]})

    if flag == ch["flag"]:
        # Time-based points: decay by 1 point per 10 seconds elapsed since registration, min 10 points
        registered_time = datetime.datetime.fromisoformat(participant["registered_at"])
        elapsed = (datetime.datetime.now() - registered_time).total_seconds()
        points = max(10, ch["points"] - int(elapsed // 10))

        solved[ch_id] = {
            "time": datetime.datetime.now().isoformat(),
            "points": points,
            "elapsed": int(elapsed)
        }
        save_scores(data)
        return jsonify({"success": True, "msg": f"Correct! +{points} points (solved in {int(elapsed)}s) 🎉", "points": points})

    return jsonify({"success": False, "msg": "Wrong flag. Try again! ❌"})


@app.route("/cookie-check")
def cookie_check():
    role = request.cookies.get("role", "guest")
    if role == "admin":
        return jsonify({"status": "Welcome admin!", "flag": "FLAG{c00ki3s_are_delic10us}"})
    resp = make_response(jsonify({
        "status": f"Access denied. You are: {role}",
        "hint": "Only admins can see the flag..."
    }))
    resp.set_cookie("role", "guest")
    return resp


def get_db():
    global DB_CONN
    if 'DB_CONN' not in globals():
        DB_CONN = sqlite3.connect(":memory:", check_same_thread=False)
        cursor = DB_CONN.cursor()
        cursor.execute("CREATE TABLE products (id INTEGER, name TEXT, description TEXT)")
        cursor.execute("CREATE TABLE secrets (flag TEXT)")
        cursor.execute("INSERT INTO products VALUES (1, 'Quantum Decryptor', 'Decrypts data stream blocks')")
        cursor.execute("INSERT INTO products VALUES (2, 'EMP Jammer', 'Short-range electromagnetic pulse generator')")
        cursor.execute("INSERT INTO products VALUES (3, 'Plasma Torch', 'Heavy duty industrial plasma cutter')")
        cursor.execute("INSERT INTO secrets VALUES ('FLAG{sqli_is_still_alive_and_kicking}')")
        DB_CONN.commit()
    return DB_CONN


@app.route("/vault-search")
def vault_search():
    query = request.args.get("query", "").strip()
    if not query:
        return jsonify({"results": []})
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Intentionally vulnerable to SQL Injection!
        sql = f"SELECT name, description FROM products WHERE name LIKE '%{query}%'"
        cursor.execute(sql)
        rows = cursor.fetchall()
        results = [{"name": r[0], "description": r[1]} for r in rows]
        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/static/files/<filename>")
def serve_file(filename):
    return send_from_directory("static/files", filename)


@app.route("/reset")
def reset():
    guard = require_login()
    if guard:
        return guard
    username = session["user"]
    data = load_scores()
    if username in data["participants"]:
        data["participants"][username]["solved"] = {}
        data["participants"][username]["registered_at"] = datetime.datetime.now().isoformat()
        save_scores(data)
    return redirect(url_for("index"))

# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USER and p == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Invalid credentials."
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
def admin_dashboard():
    guard = require_admin()
    if guard:
        return guard
    data = load_scores()
    leaderboard = compute_leaderboard(data)
    stats = build_stats(data)
    return render_template(
        "admin.html",
        challenges=CHALLENGES,
        leaderboard=leaderboard,
        stats=stats,
    )


@app.route("/admin/api/stats")
def admin_api_stats():
    guard = require_admin()
    if guard:
        return jsonify({"error": "Unauthorized"}), 403
    return api_scoreboard()


@app.route("/admin/reset", methods=["POST"])
def admin_reset():
    guard = require_admin()
    if guard:
        return jsonify({"error": "Unauthorized"}), 403
    save_scores({"participants": {}})
    return jsonify({"success": True})


@app.route("/scoreboard")
def scoreboard():
    data = load_scores()
    leaderboard = compute_leaderboard(data)
    stats = build_stats(data)
    username = session.get("user")
    solved = get_participant_solved(username) if username else {}
    return render_template(
        "scoreboard.html",
        challenges=CHALLENGES,
        leaderboard=leaderboard,
        stats=stats,
        username=username,
        solved=solved
    )


@app.route("/api/scoreboard")
def api_scoreboard():
    data = load_scores()
    leaderboard = compute_leaderboard(data)
    stats = build_stats(data)
    return jsonify({
        "leaderboard": leaderboard,
        "stats": stats,
        "challenges": {k: {"title": v["title"], "points": v["points"]} for k, v in CHALLENGES.items()},
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  CTF Challenge Server - Easy Level")
    print("  Running at: http://localhost:5000")
    print("  Admin panel: http://localhost:5000/admin/login")
    print("=" * 55 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
