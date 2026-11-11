from fastapi import HTTPException
from sqlalchemy import select

def owned(db, model, user_id, record_id):
    record = db.scalar(select(model).where(model.id == record_id, model.user_id == user_id))
    if not record: raise HTTPException(404, 'Record not found')
    return record
