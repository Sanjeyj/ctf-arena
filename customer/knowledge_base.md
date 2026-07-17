# Platform Knowledge Base
# CTF Arena v1.0.0 — EthicBids Technologies™

This document lists standard administrative configurations and troubleshooting procedures for the platform.

---

## 1. Quick Operations Reference

### Database Migrations
Verify migration status and upgrade using:
```bash
flask db current
flask db upgrade
```

### Logging Configuration
Logs are located at `/opt/ctf-arena/logs/`.
- `error.log`: Python tracebacks and exceptions.
- `access.log`: HTTP request details.

### Custom CSS Customizations
To change styles, add a custom theme inside `themes/` and set it in the configuration files instead of directly editing `ui-modernization.css`.
