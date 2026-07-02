# Native Docker Challenges

CTF Arena v2 features native hosting of containerized exploits. Competitors can spawn individual, isolated instances of a challenge.

---

## 1. How It Works

```
Competitor Click "Start Instance"
            │
            ▼
  Web Application Calls Docker SDK
            │
            ▼
  Container Spawned ──► Dynamic Port Mapped ──► Connection String Displayed
```

Containers are bound to an expiry TTL (default 30 minutes). A background task prunes expired containers every 5 minutes.

---

## 2. Admin Configuration

1. **Add Docker Image**: Go to **Admin → Docker → Images** and register the image name (e.g. `ctfarena/pwn-challenge:latest`).
2. **Create Deployment Profile**: Define CPU limits (e.g. `0.5` cores) and memory limits (e.g. `128m`) to prevent resource exhaustion attacks.
3. **Link to Challenge**: Associate the image and profile under the challenge editor settings.
