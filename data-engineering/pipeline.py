"""Run a retryable daily snapshot rebuild plus incremental raw extraction."""
import os, time, uuid
from datetime import datetime, timezone
import pandas as pd
from sqlalchemy import create_engine, text
from extraction.source import snapshot, changed
from transformation.aggregate import validate_and_normalize, aggregate, weekly_glucose, user_summary
from loading.lake import create_client, write_frame
from validation.curated import validate_curated

TABLES={'glucose':'analytics_daily_glucose','insulin':'analytics_daily_insulin','meals':'analytics_daily_carbohydrates'}
def run():
    started=datetime.now(timezone.utc); tick=time.monotonic(); batch=str(uuid.uuid4())
    engine=create_engine(os.environ['DATABASE_URL'],pool_pre_ping=True)
    s3=create_client(os.environ['MINIO_ENDPOINT'],os.environ['MINIO_ACCESS_KEY'],os.environ['MINIO_SECRET_KEY']); bucket=os.environ.get('MINIO_BUCKET','insulin-lake')
    try: s3.head_bucket(Bucket=bucket)
    except Exception: s3.create_bucket(Bucket=bucket)
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE IF NOT EXISTS pipeline_run_history (id VARCHAR(36) PRIMARY KEY, started_at TIMESTAMPTZ NOT NULL, finished_at TIMESTAMPTZ, status VARCHAR(20) NOT NULL, records_extracted INTEGER NOT NULL DEFAULT 0, records_transformed INTEGER NOT NULL DEFAULT 0, records_rejected INTEGER NOT NULL DEFAULT 0, duration_seconds DOUBLE PRECISION)'))
        conn.execute(text('CREATE TABLE IF NOT EXISTS pipeline_checkpoints (dataset VARCHAR(32) PRIMARY KEY, watermark TIMESTAMPTZ NOT NULL)'))
        conn.execute(text('CREATE TABLE IF NOT EXISTS data_quality_results (run_id VARCHAR(36), dataset VARCHAR(32), rejected_count INTEGER NOT NULL, checked_at TIMESTAMPTZ NOT NULL)'))
        conn.execute(text("INSERT INTO pipeline_run_history (id,started_at,status) VALUES (:id,:started,'running')"),{'id':batch,'started':started})
    counts={'extracted':0,'transformed':0,'rejected':0}
    try:
        with engine.connect().execution_options(isolation_level='REPEATABLE READ') as conn:
            with conn.begin():
                # Serialize runs, including manually triggered runs.
                conn.execute(text('SELECT pg_advisory_xact_lock(7641101)'))
                users, frames=snapshot(conn)
                checkpoints={row.dataset:row.watermark for row in conn.execute(text('SELECT dataset,watermark FROM pipeline_checkpoints'))}
                outputs={}; next_checkpoints={}; quality=[]
                for name,frame in frames.items():
                    delta=changed(frame,checkpoints.get(name)); counts['extracted']+=len(delta)
                    # No names, emails, or free-text notes are copied to the lake.
                    raw=delta.drop(columns=['notes'],errors='ignore')
                    key=f'raw/{name}/ingestion_date={started.date()}/batch={batch}/part.parquet'
                    if not raw.empty: write_frame(s3,bucket,key,raw)
                    valid,invalid=validate_and_normalize(name,frame,users)
                    counts['transformed']+=len(valid); counts['rejected']+=len(invalid)
                    if not invalid.empty:
                        write_frame(s3,bucket,f'quarantine/{name}/ingestion_date={started.date()}/batch={batch}/part.parquet',invalid.drop(columns=['notes'],errors='ignore'))
                    outputs[name]=aggregate(name,valid)
                    if name == 'glucose':
                        outputs['weekly']=weekly_glucose(valid)
                        outputs['summary']=user_summary(valid,started.date())
                    quality.append({'run':batch,'dataset':name,'count':len(invalid),'at':started})
                    if not frame.empty: next_checkpoints[name]=pd.to_datetime(frame['updated_at'],utc=True).max().to_pydatetime()
                # Replace all aggregates in one transaction. No overlap with operational dashboard.
                for name,table in {**TABLES,'weekly':'analytics_weekly_glucose','summary':'analytics_user_summary'}.items():
                    conn.execute(text(f'DELETE FROM {table}'))
                    out=outputs[name]
                    validate_curated(name,out)
                    if not out.empty:
                        out=out.copy(); out['refreshed_at']=started
                        out.to_sql(table,conn,if_exists='append',index=False,method='multi',chunksize=500)
                conn.execute(text('INSERT INTO data_quality_results (run_id,dataset,rejected_count,checked_at) VALUES (:run,:dataset,:count,:at)'),quality)
                for name,watermark in next_checkpoints.items():
                    conn.execute(text('INSERT INTO pipeline_checkpoints (dataset,watermark) VALUES (:dataset,:watermark) ON CONFLICT (dataset) DO UPDATE SET watermark=EXCLUDED.watermark'),{'dataset':name,'watermark':watermark})
                conn.execute(text("UPDATE pipeline_run_history SET status='success',finished_at=:finished,records_extracted=:extracted,records_transformed=:transformed,records_rejected=:rejected,duration_seconds=:duration WHERE id=:id"),{'finished':datetime.now(timezone.utc),'duration':time.monotonic()-tick,'id':batch,**counts})
    except Exception:
        with engine.begin() as conn: conn.execute(text("UPDATE pipeline_run_history SET status='failed',finished_at=:finished,duration_seconds=:duration WHERE id=:id"),{'finished':datetime.now(timezone.utc),'duration':time.monotonic()-tick,'id':batch})
        raise
    finally: engine.dispose()
    return counts
if __name__=='__main__': print(run())
