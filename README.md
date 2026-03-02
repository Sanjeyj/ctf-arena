# 🚩 CTF Arena — Easy Level

A self-hosted CTF (Capture The Flag) platform for college competitions.
All 5 easy-level challenges are included with a scoring dashboard.

---

## ⚡ Quick Start

```bash
# 1. Extract / navigate into folder
cd ctf_challenges

# 2. Run the start script
bash start.sh

# 3. Open your browser
#    http://localhost:5000
```

That's it! The server handles everything.

---

## 📋 Challenges Overview

| # | Challenge | Category | Points | Solve Method |
|---|-----------|----------|--------|--------------|
| 01 | 🔐 Caesar's Secret | Cryptography | 50 | Decode ROT-3 cipher |
| 02 | 🍪 Cookie Monster | Web Exploitation | 75 | Edit browser cookie |
| 03 | 🖼️ Hidden in Plain Sight | Steganography | 75 | `strings cat.jpg \| grep FLAG` |
| 04 | 💻 Base Jumping | Encoding | 50 | Base64 decode |
| 05 | 🔎 GitLeaks | OSINT | 100 | Read commit history |
| | **TOTAL** | | **350 pts** | |

---

## 🏁 Answer Keys (For Organizers Only)

```
CH-01: FLAG{caesar_salad_is_delicious}
CH-02: FLAG{c00ki3s_are_delic10us}
CH-03: FLAG{steg0_master_101}
CH-04: FLAG{base64_is_not_encryption}
CH-05: FLAG{git_gud_at_osint}
```

---

## 📂 Project Structure

```
ctf_challenges/
├── app.py                  # Main Flask server
├── start.sh                # Quick-start script
├── requirements.txt        # Python dependencies
├── make_stego.py           # Image generator (run once)
├── solved.json             # Auto-created: tracks scores
├── templates/
│   ├── base.html           # Shared layout
│   ├── index.html          # Dashboard
│   ├── ch_ch1.html         # Caesar cipher
│   ├── ch_ch2.html         # Cookie Monster
│   ├── ch_ch3.html         # Steganography
│   ├── ch_ch4.html         # Base64
│   └── ch_ch5.html         # OSINT/GitLeaks
└── static/
    └── files/
        └── cat.jpg         # Stego challenge image
```

---

## 🔧 Requirements

- Python 3.8+
- pip (auto-installs Flask, Pillow)
- Modern browser (Chrome/Firefox)
- Internet for Google Fonts (optional — works offline too)

---

## 🎓 Competitor Instructions

Give participants this info:

1. Open `http://localhost:5000` in your browser
2. Click any challenge to view it
3. Solve the challenge using the hints provided
4. Submit the flag in format `FLAG{...}`
5. Earn points on the scoreboard!

### Tools that may help:
- **Linux terminal** — strings, xxd, base64
- **CyberChef** — https://gchq.github.io/CyberChef
- **Browser DevTools** — F12
- **Python** — built-in libraries

---

## 🔄 Reset Progress

- Click **RESET** in the top-right navigation, OR
- Delete the `solved.json` file, OR
- Visit `http://localhost:5000/reset`

---

## 🚀 Hosting for Multiple Users

To let multiple participants on the same network connect:

```bash
# Find your local IP
ip addr show | grep "inet "   # Linux
ipconfig                       # Windows

# The server already binds to 0.0.0.0:5000
# Share your IP: http://192.168.x.x:5000
```

> ⚠️ Note: Scores are shared in this setup. For individual scoring, run a separate instance per team or integrate a database per user.

---

Made for college CTF competitions 🏆
