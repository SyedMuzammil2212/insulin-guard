# API

The interactive specification is `/docs` when the API is running. All record and analytics routes require `Authorization: Bearer <access_token>` and scope queries to the authenticated user. Times supplied to record endpoints must include UTC offset or `Z`. Collections accept `skip`, `limit` (1–200), and, for dated records, optional `start` (inclusive) and `end` (exclusive) timestamps.

- `POST /api/v1/auth/register`, `/login`, `/refresh`, `/logout`; `GET /api/v1/auth/me`.
- `GET`, `POST /api/v1/{glucose,insulin,meals,reminders}`; `GET`, `PATCH`, `DELETE /api/v1/{resource}/{id}`. PATCH validates the complete merged record.
- `PUT`, `DELETE /api/v1/profile`; `GET /api/v1/export` (CSV).
- `GET /api/v1/analytics/dashboard`, `/glucose-trends?days=7`, `/insulin-summary`, `/carbohydrate-summary`, `/weekly-report`.
- `GET /api/v1/monitoring/pipeline`, `GET /health`.

Register takes name, email and password (at least 10 characters); login returns access and refresh tokens. Refresh tokens rotate once. Logout revokes the submitted refresh token, while already-issued access tokens remain valid until expiry. A production token/session revocation design is still required. The CSV contains sensitive data; share it only with a trusted recipient. Rate limiting is a per-process development guard and is not distributed.
