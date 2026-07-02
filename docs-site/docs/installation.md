# Local Installation & Setup

Follow these steps to set up and run a CTF Arena development environment.

---

## Prerequisites

- **Python**: Version 3.10, 3.11, or 3.12.
- **Package Manager**: `pip`.
- **Database**: SQLite (built-in) or PostgreSQL.

---

## Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Sanjeyj/ctf-arena.git
   cd ctf-arena
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux / macOS
   source venv/bin/activate
   ```

3. **Install python packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database schema**:
   ```bash
   flask db upgrade
   flask seed
   ```

5. **Start Flask web server**:
   ```bash
   export FLASK_ENV=development
   flask run --port=5000
   ```

Open `http://localhost:5000` in your web browser. Default admin login is `admin` / `ctf_admin_2024`.
