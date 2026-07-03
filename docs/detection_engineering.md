# Detection Engineering Platform

This guide describes how to create, validate, and test detection rules within the CTF Arena Detection Engineering sub-module. It supports two primary industry standards: **Sigma** and **YARA**.

---

## 1. Sigma Detection Rules
Sigma is a generic, open signature format to describe log events.

### Rule Template
```yaml
title: Suspicious SSH Login Failure
logsource:
  product: linux
  service: sshd
detection:
  selection:
    action: 'login_failed'
    dest_port: 22
  condition: selection
```

### Validation
Rules are validated immediately upon creation:
- **Keys**: Title, logsource, and detection are strictly required.
- **Condition**: A matching logic statement must be defined under `detection.condition`.

### Testing
Use the testing endpoint to match the Sigma rule logic against sample normalized SIEM logs. Matches trigger security alerts automatically.

---

## 2. YARA Rules
YARA rules identify malware and malicious process memory payloads based on string or hex pattern matchers.

### Rule Template
```yara
rule Mimikatz_LSASS_Dump {
    meta:
        description = "Detects Mimikatz memory dump indicators"
    strings:
        $lsass = "lsass.exe" nocase
        $m1 = "mimikatz" nocase
    condition:
        all of them
}
```

### Validation
YARA rules are structurally validated using regular expressions to ensure correct grammar:
- Must begin with the `rule` keyword.
- Must contain a defined `condition:` section.
- Braces (`{` and `}`) must be balanced.
