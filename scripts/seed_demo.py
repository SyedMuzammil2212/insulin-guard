"""Insert synthetic demo records via the public API; never use real patient data."""
import argparse, json, urllib.request
from datetime import datetime, timedelta, timezone

def request(url, method='GET', body=None, token=None):
    headers={'Content-Type':'application/json'}
    if token: headers['Authorization']='Bearer '+token
    req=urllib.request.Request(url,method=method,headers=headers,data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req) as response: return json.load(response)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://localhost:8000/api/v1');parser.add_argument('--email',required=True);parser.add_argument('--password',required=True)
    args=parser.parse_args(); base=args.url.rstrip('/')
    request(base+'/auth/register','POST',{'name':'Synthetic Demo','email':args.email,'password':args.password})
    token=request(base+'/auth/login','POST',{'email':args.email,'password':args.password})['access_token']
    for i in range(7):
        when=(datetime.now(timezone.utc)-timedelta(days=i)).isoformat()
        request(base+'/glucose','POST',{'glucose_value':100+i*4,'unit':'mg/dL','measurement_context':'fasting','measured_at':when},token)
        request(base+'/insulin','POST',{'insulin_name':'Synthetic example','insulin_type':'long-acting','dose_units':5,'injection_site':'abdomen','administered_at':when},token)
        request(base+'/meals','POST',{'meal_name':'Synthetic breakfast','meal_type':'breakfast','carbohydrates_grams':30,'consumed_at':when},token)
    print('Created seven days of synthetic records.')
if __name__=='__main__': main()
