# Recovery Guide — Cyber Defense Platform

This manual describes how to restore the database, resolve transaction corruption, and recover service health in a disaster recovery scenario.

---

## 1. Restoring Database from Backup

Follow these steps to restore the platform state from a backup:

```bash
# 1. Stop the active Flask server process
# 2. Rename the active database to save current state
mv ctf-arena.db ctf-arena.db.corrupted

# 3. Copy the target backup database file to the workspace root
cp backups/ctf-arena_backup_YYYY-MM-DD.db ctf-arena.db

# 4. Verify integrity of the restored database
sqlite3 ctf-arena.db "PRAGMA integrity_check;"
# Expected output: ok

# 5. Verify current migration head
flask db current
# Expected head: 8bce79803ffc

# 6. Restart the application server
flask run
```

---

## 2. Recovery Verification Steps

1. **Verify Services**: Access the `/admin/operations-fabric/health` dashboard to confirm capability registry health is 100%.
2. **Review Incidents**: Confirm that any database locks or corruption events are resolved.
3. **Verify Integrity**: Run the validation script `python scripts/final_dom_certification.py` to confirm that all templates render correctly.
