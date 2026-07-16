# Documentation Guidelines — CDP v2.0

## 1. Documentation Structure

Platform documentation must follow these standards to ensure clarity and ease of maintenance:

- **Format**: Standard markdown with clean headers.
- **Reference Scheme**: Use absolute local file links (`[Label](file:///absolute/path/to/file.md)`) for internal cross-references.
- **Location**: Store all core manuals under the root `docs/` folder.

---

## 2. API Documentation

- **OpenAPI Compliance**: All HTTP route interfaces must maintain corresponding OpenAPI/Swagger definitions.
- **Auto-Generation**: API reference pages are compiled dynamically from code annotations.
- **Code Comments**: Enforce docstring comments for public functions and classes.
