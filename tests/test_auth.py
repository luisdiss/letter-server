from types import SimpleNamespace

import auth


def test_authorise_returns_user_id():
    class FakeResult:
        def scalar(self):
            return 42

    class FakeDB:
        def execute(self, query):
            return FakeResult()

    result = auth.authorise('Bearer sometoken', FakeDB())
    assert result == 42


def test_create_session_inserts_and_commits(mocker):
    fake_db = SimpleNamespace()
    fake_db.execute = mocker.Mock()
    fake_db.commit = mocker.Mock()
    mocker.patch('auth.secrets.token_hex', return_value='a11826453afd5362717affbe9c8e5b1a')

    token = auth.create_session(7, fake_db)

    assert token == 'a11826453afd5362717affbe9c8e5b1a'
    fake_db.execute.assert_called_once()
    fake_db.commit.assert_called_once()
