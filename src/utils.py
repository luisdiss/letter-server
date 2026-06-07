import hashlib
from datetime import datetime


def timestamp_to_datetime_str(timestamp: int) -> str:
    """Convert Unix timestamp to datetime string"""
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object.strftime('%Y-%m-%d %H:%M:%S')


def datetime_obj_to_timestamp(dt_object) -> int:
    """Convert datetime object to Unix timestamp"""
    return int(dt_object.timestamp())


def create_1to1_coversation_id(user_id1: int, user_id2: int) -> int:
    """Create a conversation ID from two user IDs (size compatible with postgres BIGINT)"""
    a, b = sorted([user_id1, user_id2])
    combined = f"{a}:{b}".encode('utf-8')
    digest = hashlib.sha256(combined).digest()
    return int.from_bytes(digest[:8], 'big') & 0x7FFFFFFFFFFFFFFF
