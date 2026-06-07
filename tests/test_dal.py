from unittest.mock import MagicMock, call
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from dal import insert_user


def test_insert_user_executes_and_commits():
    db = MagicMock()
    insert_user(db, 'alice', 'hashed_password')
    db.execute.assert_called_once()
    db.commit.assert_called_once()


def test_insert_user_passes_correct_values():
    db = MagicMock()
    insert_user(db, 'alice', 'hashed_password')

    _, kwargs = db.execute.call_args
    bound_params = db.execute.call_args[0][1]
    assert bound_params['username'] == 'alice'
    assert bound_params['password_hash'] == 'hashed_password'
