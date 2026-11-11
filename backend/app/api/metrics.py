"""Non-sensitive pipeline health, authenticated to limit operational exposure."""
from fastapi import APIRouter, Depends
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.core.security import current_user
from app.db.session import get_db
from app.models.entities import User
router=APIRouter()
@router.get('/api/v1/monitoring/pipeline')
def pipeline_health(user:User=Depends(current_user), db:Session=Depends(get_db)):
    if not inspect(db.get_bind()).has_table('pipeline_run_history'):
        return {'last_run':None,'last_success':None}
    columns='started_at, finished_at, status, records_extracted, records_transformed, records_rejected, duration_seconds'
    last=db.execute(text(f'SELECT {columns} FROM pipeline_run_history ORDER BY started_at DESC LIMIT 1')).mappings().first()
    success=db.execute(text("SELECT finished_at FROM pipeline_run_history WHERE status='success' ORDER BY finished_at DESC LIMIT 1")).scalar()
    return {'last_run':dict(last) if last else None,'last_success':success}
