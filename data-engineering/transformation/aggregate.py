"""Pure transformations: timestamps and analytical days are UTC."""
import pandas as pd
from datetime import timedelta

def validate_and_normalize(dataset, frame, users):
    frame = frame.copy()
    if frame.empty: return frame, frame.assign(rejection_reason=pd.Series(dtype=str))
    reasons = pd.Series('', index=frame.index, dtype='object')
    def reject(mask, reason):
        nonlocal reasons
        mask = mask.fillna(True)
        reasons = reasons.mask(mask, reasons + reason + '; ')
    reject(frame['id'].isna() | frame['user_id'].isna(), 'missing identifier')
    reject(frame.duplicated('id', keep='last'), 'duplicate identifier')
    reject(~frame['user_id'].isin(users), 'unknown user')
    date_col = {'glucose':'measured_at','insulin':'administered_at','meals':'consumed_at'}[dataset]
    frame[date_col] = pd.to_datetime(frame[date_col], utc=True, errors='coerce')
    reject(frame[date_col].isna(), 'invalid timestamp')
    value_col = {'glucose':'glucose_value','insulin':'dose_units','meals':'carbohydrates_grams'}[dataset]
    frame[value_col] = pd.to_numeric(frame[value_col], errors='coerce')
    reject(frame[value_col].isna() | (frame[value_col] < 0 if dataset == 'meals' else frame[value_col] <= 0), 'invalid quantity')
    if dataset == 'glucose':
        reject(~frame['unit'].isin(['mg/dL','mmol/L']), 'invalid glucose unit')
        frame['value_mg_dl'] = frame['glucose_value'].where(frame['unit'] == 'mg/dL', frame['glucose_value'] * 18.0182)
    frame['day'] = frame[date_col].dt.date
    invalid = frame.loc[reasons != ''].copy(); invalid['rejection_reason'] = reasons[reasons != '']
    return frame.loc[reasons == ''].copy(), invalid

def aggregate(dataset, frame):
    if frame.empty: return pd.DataFrame()
    groups = frame.groupby(['user_id','day'], as_index=False)
    if dataset == 'glucose':
        return groups.agg(average=('value_mg_dl','mean'),minimum=('value_mg_dl','min'),maximum=('value_mg_dl','max'),reading_count=('id','size'))
    if dataset == 'insulin': return groups.agg(total_units=('dose_units','sum'),injection_count=('id','size'))
    return groups.agg(total_grams=('carbohydrates_grams','sum'),meal_count=('id','size'))

def weekly_glucose(frame):
    if frame.empty: return pd.DataFrame()
    frame = frame.copy()
    stamp=pd.to_datetime(frame['day'])
    frame['week_start']=(stamp-pd.to_timedelta(stamp.dt.weekday,unit='D')).dt.date
    return frame.groupby(['user_id','week_start'],as_index=False).agg(average=('value_mg_dl','mean'),minimum=('value_mg_dl','min'),maximum=('value_mg_dl','max'),reading_count=('id','size'))

def user_summary(frame, today):
    if frame.empty: return pd.DataFrame()
    cutoff=today-timedelta(days=6)
    recent=frame[(frame['day']>=cutoff)&(frame['day']<=today)]
    if recent.empty: return pd.DataFrame()
    return recent.groupby('user_id',as_index=False).agg(days_with_readings_last_7=('day','nunique'),readings_last_7=('id','size'))
