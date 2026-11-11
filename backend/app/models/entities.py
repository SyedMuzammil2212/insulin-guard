import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Numeric, Boolean, ForeignKey, Index, CheckConstraint, Text, Date, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

def now(): return datetime.now(timezone.utc)
def uid(): return str(uuid.uuid4())

class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    preferred_glucose_unit: Mapped[str] = mapped_column(String(10), default='mg/dL')
    timezone: Mapped[str] = mapped_column(String(64), default='UTC')
    target_min: Mapped[float | None] = mapped_column(Numeric(8,2), nullable=True)
    target_max: Mapped[float | None] = mapped_column(Numeric(8,2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class Owned:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class Glucose(Owned, Base):
    __tablename__ = 'glucose_readings'
    glucose_value: Mapped[float] = mapped_column(Numeric(8,2))
    unit: Mapped[str] = mapped_column(String(10))
    measurement_context: Mapped[str] = mapped_column(String(30))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (CheckConstraint('glucose_value > 0'), CheckConstraint("unit IN ('mg/dL','mmol/L')"), Index('ix_glucose_user_time','user_id','measured_at'))

class Insulin(Owned, Base):
    __tablename__ = 'insulin_logs'
    insulin_name: Mapped[str] = mapped_column(String(120))
    insulin_type: Mapped[str] = mapped_column(String(30))
    dose_units: Mapped[float] = mapped_column(Numeric(8,2))
    injection_site: Mapped[str] = mapped_column(String(120))
    administered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (CheckConstraint('dose_units > 0'),)

class Meal(Owned, Base):
    __tablename__ = 'meal_logs'
    meal_type: Mapped[str] = mapped_column(String(20))
    meal_name: Mapped[str] = mapped_column(String(120))
    carbohydrates_grams: Mapped[float] = mapped_column(Numeric(8,2))
    consumed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    __table_args__ = (CheckConstraint('carbohydrates_grams >= 0'),)

class Reminder(Owned, Base):
    __tablename__ = 'reminders'
    reminder_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(120))
    reminder_time: Mapped[str] = mapped_column(String(5))
    timezone: Mapped[str] = mapped_column(String(64))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    jti: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

class Audit(Base):
    __tablename__ = 'audit_events'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class DailyGlucose(Base):
    __tablename__ = 'analytics_daily_glucose'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, primary_key=True)
    average: Mapped[float] = mapped_column(Numeric(10,2))
    minimum: Mapped[float] = mapped_column(Numeric(10,2))
    maximum: Mapped[float] = mapped_column(Numeric(10,2))
    reading_count: Mapped[int] = mapped_column(Integer)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class DailyInsulin(Base):
    __tablename__ = 'analytics_daily_insulin'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, primary_key=True)
    total_units: Mapped[float] = mapped_column(Numeric(10,2))
    injection_count: Mapped[int] = mapped_column(Integer)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class DailyCarbs(Base):
    __tablename__ = 'analytics_daily_carbohydrates'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, primary_key=True)
    total_grams: Mapped[float] = mapped_column(Numeric(10,2))
    meal_count: Mapped[int] = mapped_column(Integer)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class WeeklyGlucose(Base):
    __tablename__ = 'analytics_weekly_glucose'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    week_start: Mapped[datetime] = mapped_column(Date, primary_key=True)
    average: Mapped[float] = mapped_column(Numeric(10,2))
    minimum: Mapped[float] = mapped_column(Numeric(10,2))
    maximum: Mapped[float] = mapped_column(Numeric(10,2))
    reading_count: Mapped[int] = mapped_column(Integer)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class UserSummary(Base):
    __tablename__ = 'analytics_user_summary'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    days_with_readings_last_7: Mapped[int] = mapped_column(Integer)
    readings_last_7: Mapped[int] = mapped_column(Integer)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
