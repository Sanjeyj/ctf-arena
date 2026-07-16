# 🚩 CTF Arena v2

> Maintained by **[EthicBids Technologies™](https://ethicbids.vercel.app/)**

A self-hosted **Capture The Flag (CTF)** platform built with Flask for college
cybersecurity competitions. Features a **live scoreboard**, **admin dashboard**,
**Docker-based container challenges**, **time-based dynamic scoring**, **team mode**,
and a full **REST + SSE API** — all running from a single Python process.

---

## 🌐 Live Demo

> Run locally and share your LAN IP with participants — no internet required.

---

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/Sanjeyj/ctf-arena.git
cd ctf-arena

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:  venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY and ADMIN_PASSWORD

# 5. Initialise the database
flask db upgrade

# 6. (One-time) Generate the steganography challenge image
python make_stego.py

# 7. Start the development server
flask run --host=0.0.0.0 --port=5000
# or
python run.py
```

Open `http://localhost:5000` and `http://localhost:5000/admin` in your browser.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 🏠 **Challenge Dashboard** | Responsive card grid; category & difficulty filters; live solved/unsolved status |
| 📡 **Live Scoreboard** | Auto-refreshes via SSE; score distribution chart (Chart.js) |
| ⏱️ **Dynamic Scoring** | `static`, `legacy_time`, and `dynamic` decay modes |
| 🔑 **Admin Panel** | Full competition management, user/team admin, audit log |
| 🐳 **Docker Challenges** | Per-user isolated containers with automatic TTL expiry |
| 🧑‍🤝‍🧑 **Teams** | Optional team mode with per-team scoreboard |
| 💬 **Announcements** | Scheduled or immediate broadcast messages |
| 🔐 **Auth & Security** | bcrypt passwords, CSRF protection, rate limiting, session security |
| 📊 **Analytics** | Per-challenge solve rates, user activity heatmaps |
| 🔌 **Plugins** | Drop-in plugin directory for custom extensions |
| 🏅 **Certificates** | Auto-generated completion certificates |
| 📋 **Audit Log** | Immutable record of all security-relevant events |

---

## 🏁 Default Challenge Flags *(Organizers Only)*

| # | Title | Category | Flag |
|---|-------|----------|------|
| 01 | 🔐 Caesar's Secret | Cryptography | `FLAG{caesar_salad_is_delicious}` |
| 02 | 🍪 Cookie Monster | Web Exploitation | `FLAG{c00ki3s_are_delic10us}` |
| 03 | 🖼️ Hidden in Plain Sight | Steganography | `FLAG{steg0_master_101}` |
| 04 | 💻 Base Jumping | Encoding | `FLAG{base64_is_not_encryption}` |
| 05 | 🔎 GitLeaks | OSINT | `FLAG{git_gud_at_osint}` |
| 06 | 🗄️ Broken Vault | Web Exploitation | `FLAG{sqli_is_still_alive_and_kicking}` |
| 07 | 📡 Whisper Protocol | Cryptography | `FLAG{xor_ciphers_are_simple_but_effective}` |

---

## 📂 Project Structure

```
ctf-arena/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Dev / Test / Staging / Prod configs
│   ├── extensions.py        # Shared Flask extensions + helpers
│   ├── models/              # SQLAlchemy models
│   ├── repositories/        # Database query layer
│   ├── services/            # Business logic
│   ├── admin/               # Admin blueprint
│   ├── api/                 # JSON API v1 blueprint
│   ├── auth/                # Auth blueprint
│   ├── challenges/          # Challenge pages blueprint
│   ├── scoreboard/          # Live scoreboard blueprint
│   ├── docker/              # Container challenge blueprint
│   └── ...                  # (20+ additional blueprints)
├── docs/                    # Documentation
│   ├── api.md               # REST API reference
│   ├── architecture.md      # System architecture
│   ├── deployment.md        # Deployment guide
│   ├── security.md          # Security guide
│   └── admin.md             # Admin operations guide
├── migrations/              # Alembic migration scripts
├── tests/                   # pytest test suite (86 tests)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run.py                   # Dev server entry point
└── wsgi.py                  # Gunicorn entry point
```

---

## 🔧 Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| Flask | 3.0+ |
| SQLAlchemy | 2.x |
| Database | SQLite (dev) or PostgreSQL 14+ (prod) |
| Redis | 6.2+ *(optional, for multi-worker rate limiting)* |

```
pip install -r requirements.txt
```

---

## 🛡️ Admin Panel

Access: `http://localhost:5000/admin`

| Setting | Default | Env variable |
|---------|---------|--------------|
| Username | `admin` | `ADMIN_USER` |
| Password | `ctf_admin_2024` | `ADMIN_PASSWORD` |

> ⚠️ Override defaults in production via environment variables!

See [`docs/admin.md`](docs/admin.md) for the full admin operations guide.

---

## 🎓 Competitor Instructions

1. Open `http://<server-ip>:5000` in your browser.
2. Register an account.
3. Browse challenges and click a card to open one.
4. Solve the challenge and submit the flag in `FLAG{...}` format.
5. Earn points — faster solvers score more with time-decay enabled!

---

## ⚙️ Environment Variables

See [`docs/deployment.md`](docs/deployment.md) for the full variable reference.

**Minimum required for production:**

```bash
SECRET_KEY=<random 32+ char string>
ADMIN_PASSWORD=<strong password>
DATABASE_URL=postgresql://user:pass@host:5432/ctfdb  # or sqlite:///instance/ctf.db
FLASK_ENV=production
SESSION_COOKIE_SECURE=True
```

---

## 🐳 Docker

```bash
# Build and run
docker build -t ctf-arena:latest .
docker run -d -p 5000:5000 \
  -e SECRET_KEY=changeme \
  -e ADMIN_PASSWORD=changeme \
  -v $(pwd)/instance:/app/instance \
  ctf-arena:latest
```

See [`docs/deployment.md`](docs/deployment.md) for a full Docker Compose production stack example.

---

## 🧪 Running Tests

```bash
python -m pytest                    # Run all 86 tests
python -m pytest -v                 # Verbose output
python -m pytest tests/test_challenges.py  # Run a single file
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`docs/api.md`](docs/api.md) | Full REST API reference |
| [`docs/architecture.md`](docs/architecture.md) | System architecture & design |
| [`docs/deployment.md`](docs/deployment.md) | Deployment & configuration guide |
| [`docs/security.md`](docs/security.md) | Security controls & hardening |
| [`docs/admin.md`](docs/admin.md) | Admin operations guide |

---

Made with ❤️ for college cybersecurity competitions 🏆

---

&copy; 2026 **EthicBids Technologies™**. All Rights Reserved.  
Developed and Maintained by [EthicBids Technologies](https://ethicbids.vercel.app/)
