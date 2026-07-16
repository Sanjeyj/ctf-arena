# Backup Guide — Cyber Defense Platform

This guide describes the procedures for backing up the database, state parameters, and active configuration files of the Cyber Defense Platform.

---

## 1. Database Backups (SQLite)

Since the database uses SQLite, backups are performed by taking a snapshot copy of the database file.

### 1.1 Cold Backup
Stop the Flask web server worker processes before executing to prevent write lock conflicts:
```bash
# 1. Stop web server
# 2. Copy SQLite file
cp ctf-arena.db backups/ctf-arena_backup_$(date +%F_%T).db
```

### 1.2 Hot Backup (Online SQLite Backup)
To perform a backup without stopping the running application, use the SQLite Online Backup API or shell command:
```bash
sqlite3 ctf-arena.db ".backup 'backups/ctf-arena_hotbackup.db'"
```

---

## 2. Configuration & State Parameter Backups

Ensure the following configuration files are copied:
- `.env` — Holds secret key hashes and local environment variables.
- `config.py` — Application configuration file.
- `static/css/ui-modernization.css` & `static/js/ui-shell.js` — Core design system assets.

---

## 3. Scheduled Backup Policy

- **Frequency**: Perform automated backups daily.
- **Retention**: Keep daily backups for 7 days, weekly backups for 30 days, and monthly backups for 12 months.
- **Validation**: Test backup restore procedures weekly in an isolated test database container.
