# CTF Arena Plugin SDK Documentation

Welcome to the CTF Arena Plugin SDK! This document provides guidelines and APIs for extending CTF Arena's capabilities with secure, modular, and sandboxed plugins.

---

## 1. Plugin Structure

Every plugin resides in its own sub-folder inside the `plugins/` directory and must contain at least:
1. `plugin.json` (the manifest)
2. A main entry point script (e.g. `plugin.py`)

### The Manifest (`plugin.json`)
The manifest configures metadata, dependencies, and entry pathways:
```json
{
  "name": "My Discord Notifier",
  "version": "1.0.0",
  "author": "Security Team",
  "permissions": ["NETWORK_ACCESS"],
  "entry": "plugin.py"
}
```

---

## 2. The Hook Lifecycle System

Hooks allow you to inject callback listeners at specific execution checkpoints in the platform.

### Supported Hook Points

| Hook Name | Arguments Received | Description |
|---|---|---|
| `before_challenge_render` | `challenge`, `user` | Triggered before challenge details display. |
| `after_submission` | `user`, `challenge`, `correct`, `submitted_flag` | Invoked on flag submission outcomes. |
| `before_score_update` | `challenge`, `solve_count` | Allows custom override of awarded scores. |
| `after_login` | `user`, `ip_address` | Executed after successful authentication. |
| `after_team_create` | `team`, `creator` | Triggered when a new team is registered. |
| `before_container_start` | `image_ref`, `container_name` | Triggered before docker containers boot. |
| `after_container_stop` | `container_id` | Triggered after docker containers exit. |

### Hook Usage Example
To register a hook callback within your `plugin.py`:
```python
def on_user_login(user, ip_address):
    print(f"User {user.username} logged in from {ip_address}!")

def setup(api):
    api.register_hook("after_login", on_user_login)
```

---

## 3. Plugin API Registry

The `PluginAPI` wrapper exposes dynamic page, routing, and menu injection helpers.

- **`register_route(rule, endpoint, view_func, **options)`**: Adds standard Flask routing rules.
- **`register_api(rule, endpoint, view_func, **options)`**: Adds JSON REST API routes nested under `/api/v1/plugins/<plugin_name>/`.
- **`register_menu(title, endpoint)`**: Automatically registers navigation tabs inside the user dashboard.

---

## 4. Security AST Sandboxing Rules

Plugins are scanned statically on initialization to ensure system safety and guard against server-side compromise.

### Restricted Modules (AST Import Checks)
Plugins importing the following modules will be blocked completely:
- `os`
- `subprocess`
- `socket`
- `requests`
- `urllib`

### Restricted Builtin Functions (AST Call Checks)
Calls to these Python interpreters/compilers will trigger critical blocks:
- `eval()`
- `exec()`
- `compile()`

> [!CAUTION]
> Always build your extensions using standard platform helper classes. Directly querying raw sockets or initiating subprocesses will result in plugin registration failure.
