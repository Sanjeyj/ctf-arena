# Platform API Reference Manual

## 1. Authentication & Session APIs

### POST `/api/v1/auth/login`
- **Description**: Authenticates user credentials and returns a secure JWT.
- **Request Payload**:
  ```json
  { "username": "admin", "password": "..." }
  ```
- **Response**:
  ```json
  { "status": "success", "token": "eyJ..." }
  ```

---

## 2. Assurance & Trust APIs

### GET `/api/v1/assurance/cases`
- **Description**: Returns all cataloged validation cases and confidence scores.
- **Response**:
  ```json
  [
    { "id": 1, "title": "Zero Trust Access Control", "confidence_score": 92.5 }
  ]
  ```

### GET `/api/v1/assurance/devices`
- **Description**: Returns endpoint posture compliance details.

---

## 3. Operations & Observability APIs

### GET `/api/v1/operations/health`
- **Description**: Retrieves golden signals availability, latency, and throughput indices.

### GET `/api/v1/operations/incidents`
- **Description**: Lists active operational alerts and correlation logs.
