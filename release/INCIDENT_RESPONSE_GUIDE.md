# Incident Response Runbook
# CTF Arena v1.0.0 — EthicBids Technologies™

This runbook defines the triage, containment, and recovery steps for security or operational incidents affecting the CTF Arena v1.0.0 platform.

---

## 1. Incident Severity Definitions

| Severity | Impact | Example Scenario |
|----------|--------|------------------|
| **Sev 1 — Critical** | Total service outage or root compromise | Database compromise, server hijack, massive DDoS |
| **Sev 2 — Major** | Game integrity compromise or partial outage | Flag leakage, score manipulation, API brute-forcing |
| **Sev 3 — Minor** | Localized user issues or visual glitches | Typos in challenge prompts, individual account lock |

---

## 2. Threat Playbooks

### Threat A: Brute-Force Submissions
* **Symptom**: High volume of failed submissions for a specific user in `/opt/ctf-arena/logs/access.log`.
* **Action Steps**:
  1. Identify the participant's IP address from Nginx logs:
     ```bash
     docker compose -f deployment/docker-compose.production.yml logs nginx | grep "POST /submit"
     ```
  2. Temporary block via Nginx/iptables if rate-limiting fails to contain:
     ```bash
     iptables -A INPUT -s <IP_ADDRESS> -j DROP
     ```
  3. Lock the compromised account inside the Admin User ledger.

### Threat B: Flag Leakage / Solution Sharing
* **Symptom**: Multiple users solving a complex challenge within a very short time interval.
* **Action Steps**:
  1. Go to the Admin Panel -> **Submissions** and review timestamps.
  2. If leak is confirmed, edit the challenge flag value in the Admin Challenges panel:
     - Generate a new flag: `flag{new_rotated_string}`
     - Re-seed the challenge update.
  3. Solves made before the rotation are preserved, but future solves must submit the new flag.

### Threat C: Remote Code Execution / Host Compromise
* **Symptom**: Unauthorized processes running on the server, CPU spikes, files changed.
* **Action Steps**:
  1. **Immediate Containment**: Stop and isolate the entire Docker stack:
     ```bash
     docker compose -f deployment/docker-compose.production.yml down --volumes
     ```
  2. Provision a new clean instance.
  3. Audit the application logs and server access history to determine the entry point.
  4. Restore the database from the last verified daily backup (pre-compromise timestamp) using the disaster recovery runbook.

---

## 3. Communication Plan

- **Internal Notification**: Email security administrators and system owners.
- **Participant Broadcast**: Use the **Announcements** feature inside the Admin Dashboard to notify users of system status or maintenance downtime.
- **External Communications**: Directed through EthicBids Technologies corporate team.
