from datetime import datetime

from utils import timestamp_to_datetime_str, datetime_obj_to_timestamp, create_1to1_conversation_id


def test_timestamp_roundtrip():
    now = datetime.now()
    ts = datetime_obj_to_timestamp(now)
    restored = timestamp_to_datetime_str(ts)
    assert isinstance(restored, str)
    assert restored.startswith(str(now.year))


def test_conversation_id_is_symmetric():
    id1 = create_1to1_conversation_id(1, 2)
    id2 = create_1to1_conversation_id(2, 1)
    assert id1 == id2
    assert isinstance(id1, int)
