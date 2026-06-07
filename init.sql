CREATE TABLE IF NOT EXISTS users (
    user_id      SERIAL PRIMARY KEY,
    username     VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

-- One active session per user; login replaces the old token
CREATE TABLE IF NOT EXISTS sessions (
    session_token VARCHAR(255) PRIMARY KEY,
    user_id       INT UNIQUE REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id BIGINT PRIMARY KEY,
    subject         VARCHAR(255),
    created_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    message_id      SERIAL PRIMARY KEY,
    conversation_id BIGINT REFERENCES conversations(conversation_id),
    sender_id       INT REFERENCES users(user_id),
    content         TEXT,
    sent_at         TIMESTAMP,
    expiration      INT
);

CREATE TABLE IF NOT EXISTS message_recipients (
    message_id   INT REFERENCES messages(message_id),
    recipient_id INT REFERENCES users(user_id),
    is_read      BOOLEAN DEFAULT FALSE
);
