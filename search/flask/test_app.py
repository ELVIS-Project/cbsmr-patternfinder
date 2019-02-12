import pytest
import requests

ENDPOINT = 'http://127.0.0.1:5000/'

def test_root_conn():
    assert requests.get(ENDPOINT).status_code == 200

def test_index():
    res = requests.post(ENDPOINT + 'index')

    assert res.status_code == 200, "Index request failed; response\n" + str(res.content)
