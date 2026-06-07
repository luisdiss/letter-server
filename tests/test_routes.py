import json
from types import SimpleNamespace

import routes


def test_check_username_found(client, mocker):
    mocker.patch('routes.select_user_id', return_value=123)
    response = client.head('/users/alice')
    assert response.status_code == 200


def test_check_username_not_found(client, mocker):
    mocker.patch('routes.select_user_id', return_value=None)
    response = client.head('/users/alice')
    assert response.status_code == 404


def test_login_success(client, mocker):
    mocker.patch('routes.select_user_id', return_value=1)
    mocker.patch('routes.select_password_hash', return_value='fakehash')

    class FakeHasher:
        def verify(self, stored_hash, password):
            return None

    mocker.patch('routes.hasher', new=FakeHasher())
    mocker.patch('routes.create_session', return_value='auth-token')

    response = client.post('/login', json={'username': 'alice', 'password': 'password'})
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data['auth_token'] == 'auth-token'


def test_login_invalid_username_length(client):
    response = client.post('/login', json={'username': 'x' * 50, 'password': 'password'})
    assert response.status_code == 400


def test_login_username_not_found(client, mocker):
    mocker.patch('routes.select_user_id', return_value=None)
    response = client.post('/login', json={'username': 'alice', 'password': 'password'})
    assert response.status_code == 403


def test_login_wrong_password(client, mocker):
    mocker.patch('routes.select_user_id', return_value=1)
    mocker.patch('routes.select_password_hash', return_value='fakehash')

    class FakeHasher:
        def verify(self, stored_hash, password):
            raise routes.exceptions.VerifyMismatchError()

    mocker.patch('routes.hasher', new=FakeHasher())

    response = client.post('/login', json={'username': 'alice', 'password': 'password'})
    assert response.status_code == 401


def test_login_invalid_password_length(client):
    response = client.post('/login', json={'username': 'alice', 'password': ''})
    assert response.status_code == 400


def test_get_messages_unauthorised(client, mocker):
    mocker.patch('routes.authorise', return_value=None)
    response = client.get('/messages', headers={'Authorization': 'Bearer token'})
    assert response.status_code == 401


def test_get_messages_success(client, mocker):
    mocker.patch('routes.authorise', return_value=1)
    mocker.patch('routes.select_message_receipts', return_value=[SimpleNamespace(message_id=10)])
    mocker.patch('routes.select_message', return_value=SimpleNamespace(conversation_id=5, sender_id=2, content='hi', sent_at=__import__('datetime').datetime(2024, 1, 1, 0, 0), expiration=60))
    mocker.patch('routes.select_username', return_value='bob')
    mocker.patch('routes.datetime_obj_to_timestamp', return_value=1700000000)

    response = client.get('/messages', headers={'Authorization': 'Bearer token'})
    assert response.status_code == 200
    data = json.loads(response.content)
    assert data[0]['author'] == 'bob'
    assert data[0]['conversation_id'] == 5


def test_get_messages_no_receipts(client, mocker):
    mocker.patch('routes.authorise', return_value=1)
    mocker.patch('routes.select_message_receipts', return_value=[])

    response = client.get('/messages', headers={'Authorization': 'Bearer token'})
    assert response.status_code == 200
    assert json.loads(response.content) == []


def test_send_message_creates_conversation_id(client, mocker):
    mocker.patch('routes.authorise', return_value=1)
    mocker.patch('routes.select_user_id', return_value=2)
    mocker.patch('routes.conversation_exists', return_value=False)
    mocker.patch('routes.insert_conversation', return_value=None)
    mocker.patch('routes.insert_message', return_value=99)
    mocker.patch('routes.insert_message_recipient', return_value=None)
    mocker.patch('routes.create_1to1_coversation_id', return_value=12345)

    response = client.post('/messages', json={
        'conversation_id': None,
        'recipient_username': 'bob',
        'content': 'hello',
        'sent_at': 1700000000,
        'expiration': 60
    }, headers={'Authorization': 'Bearer token'})

    assert response.status_code == 200
    data = json.loads(response.content)
    assert data['conversation_id'] == 12345


def test_send_message_recipient_not_found(client, mocker):
    mocker.patch('routes.authorise', return_value=1)
    mocker.patch('routes.select_user_id', return_value=None)

    response = client.post('/messages', json={
        'conversation_id': None,
        'recipient_username': 'bob',
        'content': 'hello',
        'sent_at': 1700000000,
        'expiration': 60
    }, headers={'Authorization': 'Bearer token'})

    assert response.status_code == 404


def test_send_message_existing_conversation_returns_empty(client, mocker):
    mocker.patch('routes.authorise', return_value=1)
    mocker.patch('routes.select_user_id', return_value=2)
    mocker.patch('routes.insert_message', return_value=99)
    mocker.patch('routes.insert_message_recipient', return_value=None)

    response = client.post('/messages', json={
        'conversation_id': 123,
        'recipient_username': 'bob',
        'content': 'hello',
        'sent_at': 1700000000,
        'expiration': 60
    }, headers={'Authorization': 'Bearer token'})

    assert response.status_code == 200
    assert json.loads(response.content) == {}


def test_check_username_invalid_format(client):
    response = client.head('/users/bad_name!')
    assert response.status_code == 422


def test_register_success(client, mocker):
    mocker.patch('routes.select_user_id', return_value=None)
    mock_insert = mocker.patch('routes.insert_user')

    response = client.post('/users', json={'username': 'alice', 'password': 'password'})

    assert response.status_code == 201
    mock_insert.assert_called_once()


def test_register_username_taken(client, mocker):
    mocker.patch('routes.select_user_id', return_value=1)

    response = client.post('/users', json={'username': 'alice', 'password': 'password'})

    assert response.status_code == 409


def test_register_username_too_long(client):
    response = client.post('/users', json={'username': 'x' * 50, 'password': 'password'})
    assert response.status_code == 400


def test_register_password_too_short(client):
    response = client.post('/users', json={'username': 'alice', 'password': ''})
    assert response.status_code == 400
