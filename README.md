# Insulin Guard

A portfolio prototype for recording glucose readings, insulin administrations and meals. It includes an Expo mobile client, FastAPI API, PostgreSQL migrations and a daily analytics pipeline using Parquet, MinIO and Airflow. **Tracking and education only; this is not a medical device. It does not recommend doses, administer insulin, or adjust treatment. Discuss care and target ranges with a clinician.**

**Use synthetic data only. This is an incomplete prototype, not production-ready or assessed for healthcare regulatory compliance.** Read [security limitations](docs/security.md) before running it.

## Prerequisites

Docker Desktop with Compose, Node 22.13 or newer on the 22.x line, or Node 24.3 or newer on the 24.x line, an iOS simulator/Android emulator or Expo Go on a physical device. The pipeline image is large because it includes Java and PySpark. On a physical device the API must be reachable on your local network; the Compose API port is exposed to the host network, so use a trusted network only.

## Run locally

1. Start Docker Desktop. From the repository root create local-only random credentials:

   ```sh
   cp .env.example .env
   python3 - <<'PY'
   import base64, secrets
   from pathlib import Path
   path = Path('.env')
   s = path.read_text()
   for key in ['POSTGRES_PASSWORD', 'JWT_SECRET', 'MINIO_ROOT_PASSWORD', 'AIRFLOW_ADMIN_PASSWORD']:
       lines = s.splitlines()
       s = '\n'.join(f'{key}={secrets.token_hex(24)}' if line.startswith(key+'=') else line for line in lines) + '\n'
   s = s.replace('replace-with-fernet-key', base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())
   path.write_text(s)
   PY
   docker compose --env-file .env -f infrastructure/docker-compose.yml up --build -d
   ```

   Postgres initializes the Airflow database only on first startup of a fresh volume. API migrations run on backend startup. API documentation is at http://localhost:8000/docs, Airflow at http://localhost:8080, and MinIO console at http://localhost:9001. Airflow credentials are in `.env`.

2. In another terminal:

   ```sh
   cd mobile
   npm ci
   EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1 npx expo start
   ```

   For an Android emulator use `http://10.0.2.2:8000/api/v1`; for a physical device use the development computer's LAN IP (for example `http://192.168.1.10:8000/api/v1`). HTTP is for local synthetic data only. The server, phone, and firewall must permit the connection. Register an account, sign in, add a reading, then view it on the dashboard and glucose tab.

3. Optionally create a **new** synthetic demo account and seven days of fake records:

   ```sh
   python3 scripts/seed_demo.py --email demo@example.com --password 'choose-a-unique-demo-password'
   ```

4. In Airflow, unpause and manually trigger `insulin_analytics_pipeline`, or wait for its daily schedule. The API must have finished migrating first. Refresh the Analytics tab after completion. Raw, pseudonymous Parquet batches and quarantined invalid rows are in the MinIO bucket `insulin-lake`. The API's authenticated `/api/v1/monitoring/pipeline` endpoint provides operational status.

To stop containers without deleting data: `docker compose --env-file .env -f infrastructure/docker-compose.yml down`.

## Tests

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt pandas pyarrow boto3
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
PYTHONPATH=data-engineering .venv/bin/pytest data-engineering/tests -q
cd mobile && npm ci && npm run typecheck
```

Tests use SQLite and synthetic data; they do not substitute for PostgreSQL/MinIO/Airflow or device integration tests. The pipeline container installs the additional dependencies from `data-engineering/requirements.txt` in an isolated environment.

## Current scope and known gaps

Implemented: authenticated record CRUD and isolation, rotated refresh tokens, profile targets, live dashboard, mobile record entry/history and chart, daily device-local reminders, CSV sharing, deletion of operational and curated database records, Pandas validation and aggregation, raw/quarantine Parquet, checkpoints, quality and run metrics, and an Airflow DAG. See [pipeline details](docs/data-pipeline.md).

Not yet implemented or verified: password reset and email delivery; comprehensive mobile tests, date filtering/edit/delete UI and a full set of requested charts; activity tracking, missed-log indicators, daily chart and notification reconciliation across devices; a production timezone-aware scheduling service; deletion of a user's records from existing lake batches/backups; granular Airflow tasks; automatic Spark selection, Pandera/Great Expectations validation, and DuckDB integration; production-grade distributed rate limiting, secret management, TLS termination, monitoring, privacy controls, or healthcare compliance assessment. An npm audit reported four high-severity dependency findings in the Expo/toolchain dependency tree; review and remediate them before deployment. A standalone Spark aggregation function is supplied but is not wired into the DAG. Pipeline incremental extraction tracks database updates; aggregates are rebuilt from a full snapshot each run, not incrementally computed. Raw batch retries can create repeated objects; consumers must deduplicate by record ID and update time. Data in the lake remains after account deletion, so **never use real health data**.

See [architecture](docs/architecture.md), [API](docs/api.md), [database](docs/database.md), [pipeline](docs/data-pipeline.md), and [security](docs/security.md).
