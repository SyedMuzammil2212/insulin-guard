from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import User, RefreshToken

ph = PasswordHasher()
bearer = HTTPBearer(auto_error=False)
def check_password(password, encoded):
    try: return ph.verify(encoded, password)
    except (VerifyMismatchError, InvalidHashError): return False

def decode(token, kind):
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=['HS256'], options={'require':['exp','sub','type']})
        if data['type'] != kind: raise ValueError()
        return data
    except (jwt.PyJWTError, ValueError): raise HTTPException(401, 'Invalid or expired token')

def issue(db, user):
    now = datetime.now(timezone.utc)
    jti = str(uuid4())
    expires = now + timedelta(days=settings.refresh_days)
    db.add(RefreshToken(jti=jti, user_id=user.id, expires_at=expires))
    access = jwt.encode({'sub':user.id,'type':'access','exp':now+timedelta(minutes=settings.access_minutes)}, settings.jwt_secret, algorithm='HS256')
    refresh = jwt.encode({'sub':user.id,'type':'refresh','jti':jti,'exp':expires}, settings.jwt_secret, algorithm='HS256')
    return {'access_token':access, 'refresh_token':refresh, 'token_type':'bearer'}

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    if not credentials: raise HTTPException(401, 'Authentication required')
    data = decode(credentials.credentials, 'access')
    user = db.get(User, data['sub'])
    if not user: raise HTTPException(401, 'Authentication required')
    return user
