# Helm Chart Reference
# CTF Arena v1.0.0 — EthicBids Technologies™

This document outlines the Helm chart directory structure and values options for deploying CTF Arena v1.0.0.

---

## 1. Chart Structure

```
ctf-arena/
  Chart.yaml            # Metadata definition
  values.yaml           # Default configuration values
  templates/
    deployment.yaml     # Application deployment spec
    service.yaml        # Service definition
    ingress.yaml        # Ingress resource mapping
    secrets.yaml        # Vault or plain secret injection
    pvc.yaml            # Persistent volume claims
```

---

## 2. Values.yaml Highlights

Key parameters available in the Chart values:

```yaml
replicaCount: 2

image:
  repository: ghcr.io/your-org/ctf-arena
  pullPolicy: IfNotPresent
  tag: "1.0.0"

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: arena.your-domain.com
      paths:
        - path: /
          pathType: ImplementationSpecific

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 1000m
    memory: 1Gi
```
