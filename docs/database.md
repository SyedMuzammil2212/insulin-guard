# Database

The initial Alembic migration creates user, glucose, insulin, meal, reminder, refresh-token and audit tables, plus daily glucose/insulin/carbohydrate, weekly glucose and user-summary tables. UUIDs are stored as 36-character strings for PostgreSQL and SQLite test portability; numerical measurements use fixed precision. Foreign keys, user/time indexes and positive/nonnegative checks are present. Timestamps are UTC-aware on input. Profile targets are currently a single optional range in the preferred unit on the user table, rather than per-context target records.

The pipeline creates `pipeline_run_history`, `pipeline_checkpoints`, and `data_quality_results` operational tables on its first run. Analytical rows use user/date composite primary keys. Coverage means days with at least one valid glucose reading in the last seven UTC days; it is a description of recorded data, not adherence or a clinical goal.
