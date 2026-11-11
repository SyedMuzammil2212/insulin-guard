import os
os.environ['JWT_SECRET'] = 'test-only-secret-with-at-least-32-characters'
os.environ['DATABASE_URL'] = 'sqlite://'
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.main import app

@pytest.fixture
def client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine,expire_on_commit=False)
    def db_override():
        with sessions() as db: yield db
    app.dependency_overrides[get_db] = db_override
    with TestClient(app) as c: yield c
    app.dependency_overrides.clear(); engine.dispose()

def login(client,email):
    assert client.post('/api/v1/auth/register',json={'name':'Example','email':email,'password':'long-test-password'}).status_code == 201
    result = client.post('/api/v1/auth/login',json={'email':email,'password':'long-test-password'})
    assert result.status_code == 200
    return result.json()

def test_vertical_slice_and_isolation(client):
    a = login(client,'a@example.com'); b = login(client,'b@example.com')
    auth = {'Authorization':'Bearer '+a['access_token']}; other = {'Authorization':'Bearer '+b['access_token']}
    data = {'glucose_value':'6.2','unit':'mmol/L','measurement_context':'fasting','measured_at':'2026-01-01T08:00:00Z'}
    created = client.post('/api/v1/glucose',json=data,headers=auth)
    assert created.status_code == 201, created.text
    identifier = created.json()['id']
    assert len(client.get('/api/v1/glucose',headers=auth).json()) == 1
    assert client.get('/api/v1/glucose/'+identifier,headers=other).status_code == 404
    assert client.patch('/api/v1/glucose/'+identifier,json={'glucose_value':-1},headers=auth).status_code == 422
    assert client.delete('/api/v1/glucose/'+identifier,headers=other).status_code == 404
    assert client.get('/api/v1/analytics/dashboard',headers=auth).json()['latest_glucose']['id'] == identifier
    assert client.delete('/api/v1/glucose/'+identifier,headers=auth).status_code == 204

def test_refresh_rotation_and_validation(client):
    tokens = login(client,'rotate@example.com')
    rotated = client.post('/api/v1/auth/refresh',json={'refresh_token':tokens['refresh_token']})
    assert rotated.status_code == 200
    assert client.post('/api/v1/auth/refresh',json={'refresh_token':tokens['refresh_token']}).status_code == 401
    auth = {'Authorization':'Bearer '+rotated.json()['access_token']}
    invalid = {'glucose_value':100,'unit':'mg/dL','measurement_context':'fasting','measured_at':'2026-01-01T08:00:00'}
    assert client.post('/api/v1/glucose',json=invalid,headers=auth).status_code == 422
    assert client.get('/api/v1/analytics/glucose-trends',headers=auth).status_code == 200

def test_insulin_meals_and_account_delete(client):
    tokens = login(client,'delete@example.com'); auth = {'Authorization':'Bearer '+tokens['access_token']}
    insulin = {'insulin_name':'Example','insulin_type':'rapid-acting','dose_units':'2.5','injection_site':'abdomen','administered_at':'2026-01-01T08:00:00Z'}
    meal = {'meal_type':'breakfast','meal_name':'Example','carbohydrates_grams':'25','consumed_at':'2026-01-01T08:00:00Z'}
    assert client.post('/api/v1/insulin',headers=auth,json=insulin).status_code == 201
    assert client.post('/api/v1/meals',headers=auth,json=meal).status_code == 201
    assert client.get('/api/v1/export',headers=auth).status_code == 200
    assert client.delete('/api/v1/profile',headers=auth).status_code == 204
    assert client.get('/api/v1/auth/me',headers=auth).status_code == 401
