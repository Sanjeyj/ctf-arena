#!/usr/bin/env bash
# =============================================================================
# CTF Arena v1.0.0 — Production Restore Script
# EthicBids Technologies™
# =============================================================================
# Usage:
#   ./scripts/restore.sh --backup-dir /opt/ctf-arena/backups/20260716_120000
#   ./scripts/restore.sh --db-file /path/to/database_20260716.sql.gz
#   ./scripts/restore.sh --help
#
# IMPORTANT: This script will DROP and RECREATE the target database.
#            Always test in a staging environment first.
# =============================================================================
set -euo pipefail

POSTGRES_USER="${POSTGRES_USER:-ctfarena}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
POSTGRES_DB="${POSTGRES_DB:-ctfarena}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
APP_DIR="${APP_DIR:-/opt/ctf-arena}"
LOG_FILE="${APP_DIR}/logs/restore.log"
BACKUP_GPG_KEY="${BACKUP_GPG_KEY:-}"

BACKUP_DIR=""
DB_FILE=""
UPLOADS_FILE=""
DRY_RUN=false
SKIP_DB=false
SKIP_UPLOADS=false

# ── Argument Parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --backup-dir)   BACKUP_DIR="$2"; shift 2 ;;
    --db-file)      DB_FILE="$2"; shift 2 ;;
    --uploads-file) UPLOADS_FILE="$2"; shift 2 ;;
    --dry-run)      DRY_RUN=true; shift ;;
    --skip-db)      SKIP_DB=true; shift ;;
    --skip-uploads) SKIP_UPLOADS=true; shift ;;
    --help)
      echo "Usage: $0 --backup-dir <dir> | --db-file <file> [options]"
      echo "Options:"
      echo "  --backup-dir <dir>    Restore from a full backup directory"
      echo "  --db-file <file>      Restore database from a specific .sql.gz file"
      echo "  --uploads-file <file> Restore uploads from a specific .tar.gz file"
      echo "  --dry-run             Parse and validate backup without applying"
      echo "  --skip-db             Skip database restore"
      echo "  --skip-uploads        Skip uploads restore"
      exit 0 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

# ── Helper Functions ──────────────────────────────────────────────────────────
mkdir -p "$(dirname "${LOG_FILE}")"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"; }
fail() { log "ERROR: $*"; exit 1; }

log "=========================================="
log "CTF Arena Restore — $(date '+%Y-%m-%d %H:%M:%S')"
log "=========================================="

# ── Locate backup files if backup-dir provided ────────────────────────────────
if [[ -n "${BACKUP_DIR}" ]]; then
    [[ -d "${BACKUP_DIR}" ]] || fail "Backup directory not found: ${BACKUP_DIR}"
    DB_FILE=$(find "${BACKUP_DIR}" -name "database_*.sql.gz*" | head -1)
    UPLOADS_FILE=$(find "${BACKUP_DIR}" -name "uploads_*.tar.gz" | head -1)
fi

# ── Database Restore ──────────────────────────────────────────────────────────
restore_database() {
    [[ -z "${DB_FILE}" ]] && fail "No database backup file found/specified"
    [[ -f "${DB_FILE}" ]] || fail "Database file not found: ${DB_FILE}"

    log "Restoring database from: ${DB_FILE}"

    WORK_FILE="${DB_FILE}"

    # Decrypt if encrypted
    if [[ "${DB_FILE}" == *.gpg ]]; then
        log "Decrypting backup..."
        WORK_FILE="${DB_FILE%.gpg}"
        gpg --batch --yes --output "${WORK_FILE}" --decrypt "${DB_FILE}" || fail "GPG decrypt failed"
    fi

    # Validate
    gunzip -t "${WORK_FILE}" && log "Backup integrity: OK" || fail "Backup integrity check failed"

    if [[ "${DRY_RUN}" == "true" ]]; then
        log "[DRY RUN] Would restore database from ${WORK_FILE}"
        return
    fi

    # Stop app connections
    log "Terminating active database connections..."
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${POSTGRES_DB}' AND pid <> pg_backend_pid();" \
        >> "${LOG_FILE}" 2>&1 || log "WARNING: Could not terminate connections (non-fatal)"

    # Drop and recreate database
    log "Dropping and recreating database ${POSTGRES_DB}..."
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" \
        >> "${LOG_FILE}" 2>&1 || fail "DROP DATABASE failed"

    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" -d postgres \
        -c "CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};" \
        >> "${LOG_FILE}" 2>&1 || fail "CREATE DATABASE failed"

    # Restore
    log "Restoring data..."
    gunzip -c "${WORK_FILE}" | PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" \
        >> "${LOG_FILE}" 2>&1 || fail "psql restore failed"

    # Clean up decrypted file
    [[ "${DB_FILE}" == *.gpg ]] && rm -f "${WORK_FILE}"

    log "Database restore complete"
}

# ── Uploads Restore ───────────────────────────────────────────────────────────
restore_uploads() {
    [[ -z "${UPLOADS_FILE}" ]] && { log "No uploads backup found. Skipping."; return; }
    [[ -f "${UPLOADS_FILE}" ]] || fail "Uploads file not found: ${UPLOADS_FILE}"

    log "Restoring uploads from: ${UPLOADS_FILE}"

    if [[ "${DRY_RUN}" == "true" ]]; then
        tar -tzf "${UPLOADS_FILE}" | head -20
        log "[DRY RUN] Would restore uploads to ${APP_DIR}/uploads"
        return
    fi

    # Backup existing uploads before overwriting
    UPLOADS_BK="${APP_DIR}/uploads.bak.$(date +%s)"
    [[ -d "${APP_DIR}/uploads" ]] && mv "${APP_DIR}/uploads" "${UPLOADS_BK}"

    tar -xzf "${UPLOADS_FILE}" -C "${APP_DIR}/" >> "${LOG_FILE}" 2>&1 || fail "uploads tar extract failed"
    log "Uploads restore complete"
}

# ── Post-Restore Migrations ───────────────────────────────────────────────────
run_migrations() {
    if [[ "${DRY_RUN}" == "true" ]]; then
        log "[DRY RUN] Would run: flask db upgrade"
        return
    fi
    log "Running database migrations..."
    cd "${APP_DIR}"
    ./venv/bin/flask db upgrade >> "${LOG_FILE}" 2>&1 || log "WARNING: Migration had issues — check logs"
    log "Migrations complete"
}

# ── Main ──────────────────────────────────────────────────────────────────────
[[ "${SKIP_DB}" == "false" ]] && restore_database
[[ "${SKIP_UPLOADS}" == "false" ]] && restore_uploads
[[ "${DRY_RUN}" == "false" ]] && run_migrations

log "Restore complete"
log "IMPORTANT: Restart the application container to apply changes."
log "  docker compose -f deployment/docker-compose.production.yml restart app"
log "=========================================="
