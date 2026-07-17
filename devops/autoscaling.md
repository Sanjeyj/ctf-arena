# Autoscaling Policies
# CTF Arena v1.0.0 — EthicBids Technologies™

This document defines the Horizontal Pod Autoscaling (HPA) specifications for the application deployment in Kubernetes.

---

## 1. Horizontal Pod Autoscaler (HPA) Specification

Autoscaling is configured using standard K8s HPA objects:

- **Minimum Replicas**: 2
- **Maximum Replicas**: 10
- **Scale-Up Thresholds**:
  - CPU Utilization: **> 70% average** across all pods.
  - Memory Utilization: **> 85% average** across all pods.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ctf-arena-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ctf-arena-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 2. Cooldown & Stabilization Periods

To prevent thrashing (frequent scaling actions in a short period):
- **Scale-up stabilization**: 0 seconds (scale immediately on traffic surge).
- **Scale-down stabilization**: 300 seconds (5 minutes cooldown before reducing replica count).
