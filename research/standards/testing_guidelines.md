# Testing Guidelines & Quality Gates — CDP v2.0

## 1. Testing Pyramid

To maintain the stability of the platform, the testing strategy uses a multi-tier approach:

```
      [E2E / Integration Tests (10%)]
         [Integration Tests (30%)]
            [Unit Tests (60%)]
```

---

## 2. Quality Gates

- **Code Coverage**: Minimum test coverage of 90% is required for public interfaces.
- **Regression Tests**: Every bug fix requires a corresponding regression test case to prevent recurrence.
- **Continuous Integration**: The test suite runs automatically on code push.
- **Mocking Policy**: External integrations are simulated locally.
