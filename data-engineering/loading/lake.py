import io
import boto3

def write_frame(client, bucket, key, frame):
    buffer = io.BytesIO()
    frame.to_parquet(buffer, index=False, engine='pyarrow')
    client.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue(), ContentType='application/vnd.apache.parquet')

def create_client(endpoint, access_key, secret_key):
    return boto3.client('s3', endpoint_url=endpoint, aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name='us-east-1')
