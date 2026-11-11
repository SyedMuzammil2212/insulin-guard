import pandas as pd
from transformation.aggregate import validate_and_normalize, aggregate
from extraction.source import changed

def test_normalize_quarantine_and_aggregate():
    frame=pd.DataFrame([{'id':'1','user_id':'u','glucose_value':5.5,'unit':'mmol/L','measured_at':'2026-01-01T12:00:00Z'},{'id':'2','user_id':'u','glucose_value':100,'unit':'mg/dL','measured_at':'2026-01-01T13:00:00Z'},{'id':'3','user_id':'u','glucose_value':10,'unit':'bad','measured_at':'2026-01-01T14:00:00Z'}])
    valid,bad=validate_and_normalize('glucose',frame,{'u'})
    assert len(bad)==1 and 'invalid glucose unit' in bad.iloc[0].rejection_reason
    result=aggregate('glucose',valid).iloc[0]
    assert result.reading_count==2 and abs(result.average-99.55)<0.1

def test_duplicate_and_referential_integrity():
    row={'id':'x','user_id':'u','dose_units':2,'administered_at':'2026-01-01T12:00:00Z'}
    valid,bad=validate_and_normalize('insulin',pd.DataFrame([row,row]),{'u'})
    assert len(valid)==1 and len(bad)==1
    valid,bad=validate_and_normalize('insulin',pd.DataFrame([row]),set())
    assert valid.empty and 'unknown user' in bad.iloc[0].rejection_reason

def test_incremental_overlap_and_late_arrival():
    f=pd.DataFrame([{'id':'a','updated_at':'2026-01-02T00:00:00Z','measured_at':'2025-01-01T00:00:00Z'},{'id':'b','updated_at':'2026-01-01T00:00:00Z','measured_at':'2026-01-01T00:00:00Z'}])
    assert changed(f,'2026-01-02T00:00:00Z')['id'].tolist()==['a']

def test_weekly_and_coverage():
    from datetime import date
    from transformation.aggregate import weekly_glucose, user_summary
    rows=pd.DataFrame([{'id':'a','user_id':'u','day':date(2026,1,5),'value_mg_dl':100},{'id':'b','user_id':'u','day':date(2026,1,6),'value_mg_dl':120}])
    assert weekly_glucose(rows).iloc[0]['average']==110
    assert user_summary(rows,date(2026,1,6)).iloc[0]['days_with_readings_last_7']==2
