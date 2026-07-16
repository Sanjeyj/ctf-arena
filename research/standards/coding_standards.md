# Python Coding Standards & Conventions — CDP v2.0

## 1. Style & Guidelines

All Python development follows standardized PEP 8 formatting rules:

- **Formatting**: Enforced via Black and Flake8. Line lengths are limited to 88 characters.
- **Type Annotations**: Mandatory for all function signatures and public APIs.
- **Naming Conventions**:
  - Variables and functions use `snake_case`.
  - Class definitions use `PascalCase`.
  - Global constants use `UPPER_SNAKE_CASE`.

---

## 2. Code Quality Rules

- **Documentation**: All public classes and modules require clear docstrings.
- **Exceptions**: System flows must use specific custom exceptions instead of catching generic `Exception` wrappers.
- **Linters**: Pre-commit hooks evaluate lint rules before merges are permitted.
