# Threat Actor Curation & Intelligence

This guide describes the profiling system for threat actors within the CTF Arena Cyber Threat Intelligence workspace.

---

## 1. Actor Profile Structure
Security researchers catalog threat groups using the following parameters:
- **Aliases**: Common names given by industry vendors (e.g. Cozy Bear, APT29, Nobelium, Midnight Blizzard).
- **Motivation**: Driving force behind operations (e.g., espionage, financial, sabotage, hacktivism).
- **Sophistication**: Assessment of skill level (e.g., State-Sponsored, Organized Crime, Hacktivist, Novice).
- **Target Sectors**: Industries commonly targeted by the actor (e.g., Defense, Aviation, Critical Infrastructure).
- **Regions**: Countries of origin or geographical clusters associated with the group.

---

## 2. MITRE ATT&CK Correlation
Threat actors are linked to mapped TTPs (Tactics, Techniques, and Procedures) in the MITRE database. This helps security operations identify:
1. Mapped entry techniques (e.g., `T1190 - Exploit Public-Facing Application`).
2. Execution mechanics (e.g., `T1059 - Command and Scripting Interpreter`).
3. Defense evasion methods (e.g., `T1027 - Obfuscated Files or Information`).
4. Persistence indicators.
