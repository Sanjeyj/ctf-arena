# Deployment Guide — Cyber Defense Platform v1.0.0

## Prerequisites

- Python 3.11+ installed
- Git
- Sufficient disk space (minimum 500 MB for database and backups)

---

## 1. Initial Setup

```bash
# Clone the repository
git clone <repository_url> ctf-arena
cd ctf-arena

# Create virtual environment
python -m venv venv
source venv/bin/activate     # Linux/macOS
venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Database Initialization

```bash
# Initialize migrations
flask db upgrade

# Verify migration head
flask db current
# Expected: 8bce79803ffc (head)

# Seed initial admin and demo data
flask seed-db
```

---

## 3. Verification Before Launch

```bash
# Run full test suite (must be 1609/1609 PASS)
python -m pytest --tb=short -q

# Run smoke tests
python scripts/smoke_test.py
python scripts/admin_smoke_test.py

# Run DOM certification
python scripts/final_dom_certification.py
```

---

## 4. Launch

```bash
flask run
# Platform available at: http://127.0.0.1:5000
# Admin panel at:        http://127.0.0.1:5000/admin
```
