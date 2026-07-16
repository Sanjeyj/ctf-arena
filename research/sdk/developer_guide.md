# Plugin Developer Guide — CDP v2.0

## 1. Creating a Detection Plugin

Developers implement the `BaseDetectionPlugin` class to register custom detection engines:

```python
from cdp_sdk.detection import BaseDetectionPlugin, register_plugin

@register_plugin(name="custom_port_scanner")
class PortScanPlugin(BaseDetectionPlugin):
    def evaluate(self, log_payload: dict) -> dict:
        # Custom evaluation logic here
        return {"alert": True, "severity": "medium"}
```

---

## 2. API Hook Registration

Plugins register hooks using standard decorators:

- **Before/After Hooks**: Enforces pre-execution inputs and post-execution output validation checks.
- **Context Injection Hooks**: Allows custom metadata injection.
