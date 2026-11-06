# Module Specification: Authentication & Multi-Tenancy (auth.md)

## 1. Purpose
The Authentication module handles tenant registration, user authentication, and cryptographically secure JSON Web Token (JWT) lifecycle management. It enforces strict multi-tenancy isolation by extracting verified `tenant_id` claims and binding them into the request context for all downstream routes and services.

## 2. Files
- `app/security.py`: Direct `bcrypt` password hashing/verification and `PyJWT` encoding/decoding functions.
- `app/models/tenant.py`: SQLAlchemy table definition for `tenants`.
- `app/models/user.py`: SQLAlchemy table definition for `users`, indexed on `(tenant_id, created_at)`.
- `app/schemas/tenant.py`: Pydantic request/response models for tenants.
- `app/schemas/auth.py`: Pydantic models for user registration, login, and token responses.
- `app/services/auth_service.py`: Encapsulated business logic for registering tenants and authenticating users.
- `app/routes/auth.py`: FastAPI route handlers exposing `POST /auth/register`, `POST /auth/login`, and `GET /auth/me`.
- `app/dependencies.py`: FastAPI security dependency verifying JWT tokens and providing `CurrentUser` and `get_current_tenant`.

## 3. Inputs and Outputs

### Register (`POST /auth/register`)
- **Input:**
  ```json
  {
    "tenant_name": "Acme Corp",
    "email": "auditor@acme.com",
    "password": "SecurePassword123!",
    "role": "admin"
  }
  ```
- **Output (`201 Created`):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 3600,
    "tenant_id": "c56a4180-65aa-42ec-a945-5fd21dec0538",
    "user_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "email": "auditor@acme.com",
    "role": "admin"
  }
  ```

### Login (`POST /auth/login`)
- **Input:**
  ```json
  {
    "email": "auditor@acme.com",
    "password": "SecurePassword123!"
  }
  ```
- **Output (`200 OK`):** Same schema as Register.

### Me (`GET /auth/me`)
- **Header:** `Authorization: Bearer <access_token>`
- **Output (`200 OK`):**
  ```json
  {
    "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "tenant_id": "c56a4180-65aa-42ec-a945-5fd21dec0538",
    "email": "auditor@acme.com",
    "role": "admin"
  }
  ```

## 4. Failure Cases
- **Duplicate User Registration:** Returns `409 Conflict` with `"A user with this email address already exists."`
- **Invalid Password / Missing User:** Returns `401 Unauthorized` with `"Invalid email or password."` and `WWW-Authenticate: Bearer` header.
- **Expired or Tampered JWT:** Returns `401 Unauthorized` with `"Could not validate credentials."`
- **Malformed Input Payload:** Returns `422 Unprocessable Entity` with Pydantic validation errors.

## 5. How to Test It
Run pytest unit and integration tests:
```bash
pytest tests/test_auth.py -v
```

Manual cURL test:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"tenant_name":"Acme","email":"admin@acme.com","password":"Password123!"}'
```

## 6. Known Limits
- Refresh tokens are omitted in MVP; sessions expire based on `JWT_EXPIRE_MINUTES`.
- Password reset and email confirmation flows are scheduled for Phase 2.
