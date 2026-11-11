from datetime import datetime
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

Unit = Literal['mg/dL', 'mmol/L']
class Register(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
class Login(BaseModel):
    email: EmailStr
    password: str
class TokenBody(BaseModel):
    refresh_token: str
class Profile(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    preferred_glucose_unit: Unit
    timezone: str
    target_min: Decimal | None = Field(default=None, gt=0)
    target_max: Decimal | None = Field(default=None, gt=0)
    @field_validator('timezone')
    @classmethod
    def timezone_valid(cls, v):
        try: ZoneInfo(v)
        except ZoneInfoNotFoundError: raise ValueError('Invalid IANA timezone')
        return v
    @model_validator(mode='after')
    def targets_valid(self):
        if (self.target_min is None) != (self.target_max is None): raise ValueError('Both target values are required')
        if self.target_min is not None and self.target_min >= self.target_max: raise ValueError('Target minimum must be less than maximum')
        return self
class Record(BaseModel):
    model_config = ConfigDict(extra='forbid')
    @field_validator('*', mode='after')
    @classmethod
    def aware_datetimes(cls, value):
        if isinstance(value, datetime) and (value.tzinfo is None or value.utcoffset() is None): raise ValueError('Timestamp must include an offset')
        return value
class GlucoseIn(Record):
    glucose_value: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    unit: Unit
    measurement_context: Literal['fasting','before_meal','after_meal','bedtime','other']
    measured_at: datetime
    notes: str | None = Field(default=None, max_length=2000)
class InsulinIn(Record):
    insulin_name: str = Field(min_length=1, max_length=120)
    insulin_type: Literal['rapid-acting','short-acting','intermediate-acting','long-acting']
    dose_units: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    injection_site: str = Field(min_length=1, max_length=120)
    administered_at: datetime
    notes: str | None = Field(default=None, max_length=2000)
class MealIn(Record):
    meal_type: Literal['breakfast','lunch','dinner','snack']
    meal_name: str = Field(min_length=1, max_length=120)
    carbohydrates_grams: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    consumed_at: datetime
    notes: str | None = Field(default=None, max_length=2000)
class ReminderIn(Record):
    reminder_type: Literal['insulin','glucose','custom']
    title: str = Field(min_length=1, max_length=120)
    reminder_time: str = Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$')
    timezone: str
    enabled: bool = True
    @field_validator('timezone')
    @classmethod
    def timezone_valid(cls, v):
        try: ZoneInfo(v)
        except ZoneInfoNotFoundError: raise ValueError('Invalid IANA timezone')
        return v
