import os
import json
import datetime
import sqlite3
from flask import current_app

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

DB_CONN = None

def get_legacy_db():
    global DB_CONN
    if DB_CONN is None:
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

def load_scores():
    scores_file = current_app.config["SCORES_FILE"]
    if os.path.exists(scores_file):
        with open(scores_file, encoding='utf-8') as f:
            return json.load(f)
    return {"participants": {}}

def save_scores(data):
    scores_file = current_app.config["SCORES_FILE"]
    with open(scores_file, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_participant_solved(username):
    data = load_scores()
    return data["participants"].get(username, {}).get("solved", {})

def compute_leaderboard(data):
    board = []
    for name, info in data["participants"].items():
        solved = info.get("solved", {})
        total_pts = sum(v["points"] for v in solved.values() if v.get("points") is not None)
        solve_count = len(solved)
        times = [v["time"] for v in solved.values() if "time" in v]
        last_solve = max(times) if times else info.get("registered_at", "")
        board.append({
            "name": name,
            "score": total_pts,
            "solve_count": solve_count,
            "solved": solved,
            "registered_at": info.get("registered_at", ""),
            "last_solve": last_solve,
        })
    board.sort(key=lambda x: (-x["score"], x["last_solve"]))
    for i, entry in enumerate(board):
        entry["rank"] = i + 1
    return board

def build_stats(data):
    participants = data["participants"]
    total_participants = len(participants)
    total_solves = sum(len(p.get("solved", {})) for p in participants.values())

    ch_solve_counts = {ch_id: 0 for ch_id in CHALLENGES}
    for p in participants.values():
        for ch_id in p.get("solved", {}):
            if ch_id in ch_solve_counts:
                ch_solve_counts[ch_id] += 1

    most_popular = max(ch_solve_counts, key=ch_solve_counts.get) if ch_solve_counts and any(ch_solve_counts.values()) else None
    max_possible = sum(c["points"] for c in CHALLENGES.values())

    return {
        "total_participants": total_participants,
        "total_solves": total_solves,
        "ch_solve_counts": ch_solve_counts,
        "most_popular_ch": CHALLENGES[most_popular]["title"] if most_popular else "—",
        "max_possible": max_possible,
    }
