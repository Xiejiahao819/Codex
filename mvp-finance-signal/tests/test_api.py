from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json() == {'status': 'ok'}


def test_list_events():
    resp = client.get('/events')
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_event_404():
    resp = client.get('/events/999')
    assert resp.status_code == 404


def test_company_decompose():
    resp = client.get('/companies/1810.HK/decompose')
    assert resp.status_code == 200
    body = resp.json()
    assert body['ticker'] == '1810.HK'
    assert body['direct_industry'] == '智能汽车'
