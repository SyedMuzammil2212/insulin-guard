"""Optional Spark implementation for glucose records too large for Pandas.

Call with an already validated Spark DataFrame. The production-sized execution
and quarantine path are not wired into the Airflow DAG yet.
"""
from pyspark.sql import functions as F

def aggregate_glucose(frame):
    normalized=frame.withColumn('value_mg_dl',F.when(F.col('unit')=='mmol/L',F.col('glucose_value')*F.lit(18.0182)).otherwise(F.col('glucose_value'))).withColumn('day',F.to_date(F.col('measured_at')))
    return normalized.groupBy('user_id','day').agg(F.avg('value_mg_dl').alias('average'),F.min('value_mg_dl').alias('minimum'),F.max('value_mg_dl').alias('maximum'),F.count('*').alias('reading_count'))
