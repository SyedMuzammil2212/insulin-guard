"""Assertions enforced before replacing the curated tables."""
def validate_curated(name, frame):
    if frame.empty: return
    keys=['user_id'] if name=='summary' else ['user_id','week_start' if name=='weekly' else 'day']
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError(f'{name}: null or duplicate aggregate keys')
    counts={'glucose':'reading_count','insulin':'injection_count','meals':'meal_count','weekly':'reading_count','summary':'readings_last_7'}
    if (frame[counts[name]] <= 0).any(): raise ValueError(f'{name}: invalid count')
