"""Extract a stable full snapshot for aggregates and changed rows for raw storage.

A full snapshot deliberately incorporates edits, deletions, and late-arriving events.
"""
import pandas as pd
from sqlalchemy import text
TABLES = {'glucose':'glucose_readings','insulin':'insulin_logs','meals':'meal_logs'}

def snapshot(connection):
    users = set(pd.read_sql_query(text('SELECT id FROM users'),connection)['id'])
    frames = {name:pd.read_sql_query(text(f'SELECT * FROM {table} ORDER BY updated_at, id'),connection) for name,table in TABLES.items()}
    return users,frames

def changed(frame, checkpoint):
    if frame.empty or checkpoint is None: return frame.copy()
    # Inclusive overlap makes equal timestamps and restarts safe; IDs deduplicate downstream.
    timestamps = pd.to_datetime(frame['updated_at'],utc=True)
    return frame.loc[timestamps >= pd.Timestamp(checkpoint)].copy()
