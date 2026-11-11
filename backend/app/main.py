import csv, io, time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import check_password, current_user, decode, issue, ph
from app.db.session import get_db
from app.models.entities import User, Glucose, Insulin, Meal, Reminder, RefreshToken, DailyGlucose, DailyInsulin, DailyCarbs, WeeklyGlucose, UserSummary
from app.repositories.records import owned
from app.schemas.records import Register, Login, TokenBody, Profile, GlucoseIn, InsulinIn, MealIn, ReminderIn
from app.services.records import audit

app = FastAPI(title='Insulin Guard API', version='1.0.0')
if settings.cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(','), allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
# Local development guard only: use a shared, proxy-aware rate limiter in production.
attempts = defaultdict(deque)
@app.middleware('http')
async def rate_limit(request: Request, call_next):
    if request.url.path in ('/api/v1/auth/login','/api/v1/auth/register','/api/v1/auth/refresh'):
        key = request.client.host if request.client else 'unknown'
        window = attempts[key]; now = time.monotonic()
        while window and window[0] < now-60: window.popleft()
        if len(window) >= 30: return Response(status_code=429, content='Too many requests')
        window.append(now)
    return await call_next(request)

@app.get('/health')
def health(): return {'status':'ok'}

def public_user(u):
    return {k:getattr(u,k) for k in ('id','name','email','preferred_glucose_unit','timezone','target_min','target_max','created_at')}

@app.post('/api/v1/auth/register', status_code=201)
def register(data: Register, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)): raise HTTPException(409, 'Email already registered')
    user = User(name=data.name, email=email, password_hash=ph.hash(data.password))
    db.add(user); db.flush(); audit(db,user.id,'register'); db.commit()
    return public_user(user)

@app.post('/api/v1/auth/login')
def login(data: Login, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not check_password(data.password,user.password_hash): raise HTTPException(401,'Invalid credentials')
    tokens = issue(db,user); audit(db,user.id,'login'); db.commit(); return tokens

@app.post('/api/v1/auth/refresh')
def refresh(data: TokenBody, db: Session = Depends(get_db)):
    token = decode(data.refresh_token,'refresh')
    result = db.execute(update(RefreshToken).where(RefreshToken.jti == token.get('jti'), RefreshToken.user_id == token['sub'], RefreshToken.revoked.is_(False)).values(revoked=True))
    if result.rowcount != 1: raise HTTPException(401,'Invalid or revoked refresh token')
    user = db.get(User,token['sub'])
    if not user: raise HTTPException(401,'Invalid refresh token')
    tokens = issue(db,user); db.commit(); return tokens

@app.post('/api/v1/auth/logout', status_code=204)
def logout(data: TokenBody, user: User = Depends(current_user), db: Session = Depends(get_db)):
    token = decode(data.refresh_token,'refresh')
    if token['sub'] != user.id: raise HTTPException(403,'Invalid token')
    db.execute(update(RefreshToken).where(RefreshToken.jti == token.get('jti'), RefreshToken.user_id == user.id).values(revoked=True)); audit(db,user.id,'logout'); db.commit()
    return Response(status_code=204)

@app.get('/api/v1/auth/me')
def me(user: User = Depends(current_user)): return public_user(user)

@app.put('/api/v1/profile')
def profile(data: Profile, user: User = Depends(current_user), db: Session = Depends(get_db)):
    for k,v in data.model_dump().items(): setattr(user,k,v)
    audit(db,user.id,'profile.update'); db.commit(); return public_user(user)

@app.delete('/api/v1/profile', status_code=204)
def delete_account(user: User = Depends(current_user), db: Session = Depends(get_db)):
    # Explicit deletes also work with SQLite's default foreign-key configuration.
    for model in (Glucose,Insulin,Meal,Reminder,RefreshToken,DailyGlucose,DailyInsulin,DailyCarbs,WeeklyGlucose,UserSummary): db.execute(delete(model).where(model.user_id == user.id))
    audit(db,user.id,'account.delete'); db.delete(user); db.commit(); return Response(status_code=204)

@app.get('/api/v1/export')
def export(user: User = Depends(current_user), db: Session = Depends(get_db)):
    output = io.StringIO(); writer = csv.writer(output); writer.writerow(['record_type','id','timestamp','details'])
    for model, date, fields in [(Glucose,'measured_at',('glucose_value','unit','measurement_context','notes')),(Insulin,'administered_at',('insulin_name','insulin_type','dose_units','injection_site','notes')),(Meal,'consumed_at',('meal_type','meal_name','carbohydrates_grams','notes'))]:
        for row in db.scalars(select(model).where(model.user_id == user.id)):
            writer.writerow([model.__tablename__,row.id,getattr(row,date).isoformat(),'; '.join(f'{f}={getattr(row,f)}' for f in fields)])
    audit(db,user.id,'data.export'); db.commit(); output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type='text/csv', headers={'Content-Disposition':'attachment; filename="health-records.csv"'})

def mount_crud(path, model, schema, date_field):
    def create(body, user: User = Depends(current_user), db: Session = Depends(get_db)):
        row = model(user_id=user.id, **body.model_dump()); db.add(row); audit(db,user.id,f'{path}.create'); db.commit(); db.refresh(row); return row
    create.__annotations__['body'] = schema
    def listing(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), start: datetime | None = None, end: datetime | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
        q = select(model).where(model.user_id == user.id)
        if date_field:
            field = getattr(model,date_field)
            if start: q = q.where(field >= start)
            if end: q = q.where(field < end)
            q = q.order_by(field.desc(),model.id.desc())
        else: q = q.order_by(model.created_at.desc())
        return list(db.scalars(q.offset(skip).limit(limit)))
    def get_one(record_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)): return owned(db,model,user.id,record_id)
    def patch(record_id: str, body: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
        row = owned(db,model,user.id,record_id)
        current = {name:getattr(row,name) for name in schema.model_fields}
        try: data = schema.model_validate({**current,**body})
        except Exception as exc:
            from pydantic import ValidationError
            if isinstance(exc,ValidationError): raise HTTPException(422,detail=exc.errors(include_context=False, include_input=False))
            raise
        for k,v in data.model_dump().items(): setattr(row,k,v)
        audit(db,user.id,f'{path}.update'); db.commit(); db.refresh(row); return row
    def remove(record_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
        row = owned(db,model,user.id,record_id); db.delete(row); audit(db,user.id,f'{path}.delete'); db.commit(); return Response(status_code=204)
    root = '/api/v1/'+path
    app.add_api_route(root,create,methods=['POST'],status_code=201,name=f'{path}_create')
    app.add_api_route(root,listing,methods=['GET'],name=f'{path}_list')
    app.add_api_route(root+'/{record_id}',get_one,methods=['GET'],name=f'{path}_get')
    app.add_api_route(root+'/{record_id}',patch,methods=['PATCH'],name=f'{path}_patch')
    app.add_api_route(root+'/{record_id}',remove,methods=['DELETE'],status_code=204,name=f'{path}_delete')

for args in [('glucose',Glucose,GlucoseIn,'measured_at'),('insulin',Insulin,InsulinIn,'administered_at'),('meals',Meal,MealIn,'consumed_at'),('reminders',Reminder,ReminderIn,None)]: mount_crud(*args)

@app.get('/api/v1/analytics/dashboard')
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    tz = ZoneInfo(user.timezone); local_now = datetime.now(tz); start = local_now.replace(hour=0,minute=0,second=0,microsecond=0).astimezone(timezone.utc); end = (local_now.replace(hour=0,minute=0,second=0,microsecond=0)+timedelta(days=1)).astimezone(timezone.utc)
    glucose = list(db.scalars(select(Glucose).where(Glucose.user_id == user.id).order_by(Glucose.measured_at.desc()).limit(100)))
    insulin = list(db.scalars(select(Insulin).where(Insulin.user_id == user.id, Insulin.administered_at >= start, Insulin.administered_at < end)))
    meals = list(db.scalars(select(Meal).where(Meal.user_id == user.id, Meal.consumed_at >= start, Meal.consumed_at < end)))
    last_insulin = db.scalar(select(Insulin).where(Insulin.user_id == user.id).order_by(Insulin.administered_at.desc()).limit(1))
    reminders = list(db.scalars(select(Reminder).where(Reminder.user_id == user.id, Reminder.enabled.is_(True))))
    return {'latest_glucose':glucose[0] if glucose else None,'last_insulin':last_insulin,'today_insulin_units':sum(float(x.dose_units) for x in insulin),'today_carbohydrates_grams':sum(float(x.carbohydrates_grams) for x in meals),'reminders':reminders,'recent_glucose':glucose,'as_of':datetime.now(timezone.utc)}

@app.get('/api/v1/analytics/glucose-trends')
def glucose_trends(days: int = Query(7,ge=1,le=366), user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = list(db.scalars(select(DailyGlucose).where(DailyGlucose.user_id == user.id, DailyGlucose.day >= datetime.now(timezone.utc).date()-timedelta(days=days-1)).order_by(DailyGlucose.day)))
    return {'data': rows, 'unit':'mg/dL', 'freshness':max((r.refreshed_at for r in rows),default=None), 'source':'curated'}

@app.get('/api/v1/analytics/insulin-summary')
def insulin_summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = list(db.scalars(select(DailyInsulin).where(DailyInsulin.user_id == user.id).order_by(DailyInsulin.day.desc()).limit(90)))
    return {'data':rows,'freshness':max((r.refreshed_at for r in rows),default=None),'source':'curated'}

@app.get('/api/v1/analytics/carbohydrate-summary')
def carbohydrate_summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = list(db.scalars(select(DailyCarbs).where(DailyCarbs.user_id == user.id).order_by(DailyCarbs.day.desc()).limit(90)))
    return {'data':rows,'freshness':max((r.refreshed_at for r in rows),default=None),'source':'curated'}

@app.get('/api/v1/analytics/weekly-report')
def weekly_report(user: User = Depends(current_user), db: Session = Depends(get_db)):
    cutoff=datetime.now(timezone.utc).date()-timedelta(days=6)
    insulin=list(db.scalars(select(DailyInsulin).where(DailyInsulin.user_id == user.id,DailyInsulin.day >= cutoff).order_by(DailyInsulin.day)))
    carbs=list(db.scalars(select(DailyCarbs).where(DailyCarbs.user_id == user.id,DailyCarbs.day >= cutoff).order_by(DailyCarbs.day)))
    return {'glucose':glucose_trends(7,user,db),'insulin':insulin,'carbohydrates':carbs,'coverage':db.get(UserSummary,user.id)}

from app.api.metrics import router as metrics_router
app.include_router(metrics_router)
