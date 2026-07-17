#!/usr/bin/env bash
# =============================================================================
# CTF Arena v1.0.0 — Production Backup Script
# EthicBids Technologies™
# =============================================================================
# Usage:
#   chmod +x scripts/backup.sh
#   ./scripts/backup.sh                  # Full backup
#   ./scripts/backup.sh --db-only        # Database only
#   ./scripts/backup.sh --uploads-only   # Uploads only
#
# Environment variables (set in .env or export before running):
#   BACKUP_DIR        — destination directory (default: /opt/ctf-arena/backups)
#   POSTGRES_USER     — database user
#   POSTGRES_PASSWORD — database password
#   POSTGRES_DB       — database name
#   POSTGRES_HOST     — database host (default: localhost)
#   BACKUP_ENCRYPT    — set to 'true' to encrypt with GPG
#   BACKUP_GPG_KEY    — GPG key ID or email for encryption
#   BACKUP_S3_BUCKET  — optional: S3 bucket URI (e.g. s3://my-bucket/ctf-arena)
# =============================================================================
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
BACKUP_DIR="${BACKUP_DIR:-/opt/ctf-arena/backups}"
POSTGRES_USER="${POSTGRES_USER:-ctfarena}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
POSTGRES_DB="${POSTGRES_DB:-ctfarena}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
APP_DIR="${APP_DIR:-/opt/ctf-arena}"
BACKUP_ENCRYPT="${BACKUP_ENCRYPT:-false}"
BACKUP_GPG_KEY="${BACKUP_GPG_KEY:-}"
BACKUP_S3_BUCKET="${BACKUP_S3_BUCKET:-}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"
LOG_FILE="${BACKUP_DIR}/backup.log"

DB_ONLY=false
UPLOADS_ONLY=false

# ── Argument Parsing ──────────────────────────────────────────────────────────
for arg in "$@"; do
  case $arg in
    --db-only)      DB_ONLY=true ;;
    --uploads-only) UPLOADS_ONLY=true ;;
  esac
done

# ── Helper Functions ──────────────────────────────────────────────────────────
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_FILE}"; }
fail() { log "ERROR: $*"; exit 1; }

# ── Pre-flight Checks ─────────────────────────────────────────────────────────
log "=========================================="
log "CTF Arena Backup — ${TIMESTAMP}"
log "=========================================="

mkdir -p "${BACKUP_PATH}"
log "Backup directory: ${BACKUP_PATH}"

# ── Database Backup ───────────────────────────────────────────────────────────
backup_database() {
    log "Starting database backup..."

    if [[ -z "${POSTGRES_PASSWORD}" ]]; then
        fail "POSTGRES_PASSWORD is not set"
    fi

    DB_DUMP="${BACKUP_PATH}/database_${TIMESTAMP}.sql"
    DB_DUMP_GZ="${DB_DUMP}.gz"

    PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --no-password \
        --verbose \
        --format=plain \
        --encoding=UTF8 \
        > "${DB_DUMP}" 2>> "${LOG_FILE}" || fail "pg_dump failed"

    gzip -9 "${DB_DUMP}"
    log "Database backup: ${DB_DUMP_GZ} ($(du -sh "${DB_DUMP_GZ}" | cut -f1))"

    # Encrypt if configured
    if [[ "${BACKUP_ENCRYPT}" == "true" ]]; then
        [[ -z "${BACKUP_GPG_KEY}" ]] && fail "BACKUP_GPG_KEY must be set when BACKUP_ENCRYPT=true"
        gpg --batch --yes --encrypt --recipient "${BACKUP_GPG_KEY}" "${DB_DUMP_GZ}"
        rm -f "${DB_DUMP_GZ}"
        log "Database backup encrypted: ${DB_DUMP_GZ}.gpg"
    fi

    # Verify backup integrity
    if [[ "${BACKUP_ENCRYPT}" != "true" ]]; then
        gunzip -t "${DB_DUMP_GZ}" && log "Database backup integrity: OK" || fail "Backup integrity check failed"
    fi
}

# ── Uploads Backup ────────────────────────────────────────────────────────────
backup_uploads() {
    log "Starting uploads backup..."

    UPLOADS_DIR="${APP_DIR}/uploads"
    UPLOADS_ARCHIVE="${BACKUP_PATH}/uploads_${TIMESTAMP}.tar.gz"

    if [[ ! -d "${UPLOADS_DIR}" ]]; then
        log "WARNING: Uploads directory not found at ${UPLOADS_DIR}. Skipping."
        return
    fi

    tar -czf "${UPLOADS_ARCHIVE}" -C "${APP_DIR}" uploads/ 2>> "${LOG_FILE}" || fail "uploads tar failed"
    log "Uploads backup: ${UPLOADS_ARCHIVE} ($(du -sh "${UPLOADS_ARCHIVE}" | cut -f1))"
}

# ── Configuration Backup ──────────────────────────────────────────────────────
backup_config() {
    log "Starting configuration backup..."

    CONFIG_ARCHIVE="${BACKUP_PATH}/config_${TIMESTAMP}.tar.gz"

    # Only backup non-sensitive config structure (not .env.production itself)
    tar -czf "${CONFIG_ARCHIVE}" \
        -C "${APP_DIR}" \
        --exclude='.env.production' \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        deployment/ \
        .env.production.example \
        pyproject.toml \
        requirements.txt \
        2>> "${LOG_FILE}" || fail "config tar failed"

    log "Config backup: ${CONFIG_ARCHIVE} ($(du -sh "${CONFIG_ARCHIVE}" | cut -f1))"
}

# ── S3 Upload ─────────────────────────────────────────────────────────────────
upload_to_s3() {
    if [[ -z "${BACKUP_S3_BUCKET}" ]]; then
        return
    fi
    log "Uploading backups to S3: ${BACKUP_S3_BUCKET}..."
    aws s3 sync "${BACKUP_PATH}/" "${BACKUP_S3_BUCKET}/${TIMESTAMP}/" \
        --storage-class STANDARD_IA \
        2>> "${LOG_FILE}" || log "WARNING: S3 upload failed (non-fatal)"
    log "S3 upload complete"
}

# ── Retention Cleanup ─────────────────────────────────────────────────────────
cleanup_old_backups() {
    log "Cleaning up backups older than ${RETENTION_DAYS} days..."
    find "${BACKUP_DIR}" -mindepth 1 -maxdepth 1 -type d -mtime "+${RETENTION_DAYS}" -exec rm -rf {} + 2>/dev/null || true
    log "Cleanup complete"
}

# ── Main ──────────────────────────────────────────────────────────────────────
if [[ "${UPLOADS_ONLY}" == "true" ]]; then
    backup_uploads
elif [[ "${DB_ONLY}" == "true" ]]; then
    backup_database
else
    backup_database
    backup_uploads
    backup_config
fi

upload_to_s3
cleanup_old_backups

log "Backup complete: ${BACKUP_PATH}"
log "=========================================="
