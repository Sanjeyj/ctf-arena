# Tool Installation Report — Cyber Defense Platform
# EthicBids Technologies™ | 2026-07-17

---

## Installation Overview

Due to administrative permission restrictions preventing the installation/removal of the system-wide custom Node.js v24.15.0 package, we successfully deployed a fully isolated, portable Node.js LTS environment locally in the workspace directory.

---

## Tool Details

| Tool | Installation Type | Version | Execution Path |
|---|---|---|---|
| **Node.js** | Portable LTS Binary (Unzipped) | `v22.23.1` | `d:\CTFd\CTF\ctf-arena\.node\node-v22.23.1-win-x64\node.exe` |
| **npm** | Portable LTS Bundled | `10.9.8` | `d:\CTFd\CTF\ctf-arena\.node\node-v22.23.1-win-x64\npm.cmd` |
| **Vercel CLI** | Global Prefix Local Package | `56.3.1` | `d:\CTFd\CTF\ctf-arena\.node\node-v22.23.1-win-x64\vercel.cmd` |

---

## Verification Commands & Outputs

### Node.js Verification
```bash
> node -v
v22.23.1
```

### npm Verification
```bash
> npm -v
10.9.8
```

### Vercel CLI Verification
```bash
> vercel --version
Vercel CLI 56.3.1
```

---

## Next Steps
All Vercel deployment commands will route through this verified local execution path.
