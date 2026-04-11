from fastapi.testclient import TestClient

from auth_svc.main import create_app


def test_auth_signup_signin_and_me() -> None:
    client = TestClient(create_app())

    signup = client.post(
        '/auth/signup',
        json={'email': 'member@example.com', 'password': 'Password123', 'first_name': 'Mia'},
    )
    assert signup.status_code == 201
    assert signup.json()['user']['email'] == 'member@example.com'

    signin = client.post('/auth/signin', json={'email': 'member@example.com', 'password': 'Password123'})
    assert signin.status_code == 200
    token = signin.json()['access_token']

    me = client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me.status_code == 200
    assert me.json()['email'] == 'member@example.com'
