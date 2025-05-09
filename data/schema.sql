-- data/schema.sql
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS system_messages;

-- data/schema.sql
-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Messages Table (Example Feature)
CREATE TABLE IF NOT EXISTS system_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL, -- Link system messages to users
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
-- Optional: Add unique constraint for name per user
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_system_messages_user_name ON system_messages (user_id, name);


-- Chat History Table (Placeholder - Add later)
-- CREATE TABLE IF NOT EXISTS chat_histories ( ... );

-- Chat Messages Table (Placeholder - Add later)
-- CREATE TABLE IF NOT EXISTS chat_messages ( ... );

-- JWT Blocklist Table (Optional - Add if implementing refresh token revocation)
-- CREATE TABLE IF NOT EXISTS token_blocklist ( ... );