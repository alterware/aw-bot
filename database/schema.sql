CREATE TABLE IF NOT EXISTS message_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regex TEXT NOT NULL,
    response TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER PRIMARY KEY,
    role_id INTEGER NOT NULL,
    date_assigned TEXT,
    user_name TEXT
);

CREATE TABLE IF NOT EXISTS black_list (
    user_id INTEGER PRIMARY KEY,
    date_assigned TEXT,
    reason TEXT
);
