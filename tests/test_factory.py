from api import create_app
import json

def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_hello(client):
    response = client.get('/hello')
    assert json.loads(response.data) == 'Hello, World!!'
