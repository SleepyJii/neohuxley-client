import sqlite3
from contextlib import contextmanager
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from utils.config import APP_ROOT


class Database:
    def __init__(self, db_path: str = f"{APP_ROOT}/activitypub.db"):
        self.db_path = Path(db_path)
        self._init_schema()
        self._ensure_host_user()

    def _init_schema(self):
        with self.connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS inbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivered INTEGER DEFAULT 0,
                delivery_error TEXT
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS keys (
                user_id INTEGER PRIMARY KEY,
                public_key TEXT NOT NULL,
                private_key TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)
            conn.commit()

    def _ensure_host_user(self):
        if not self.check_user('host'):
            print('[DB] creating `host` user')
            self.create_user('host')

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def insert_inbox(self, data: str):
        with self.connect() as conn:
            conn.execute("INSERT INTO inbox (data) VALUES (?)", (data,))
            conn.commit()

    def insert_outbox(self, activity_data: str, activity_id: str):
        with self.connect() as conn:
            conn.execute("INSERT INTO outbox (activity_id, data) VALUES (?, ?)", (activity_id, activity_data,))
            conn.commit()

    def get_inbox(self, limit: int = 10):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM inbox ORDER BY received_at DESC LIMIT ?", (limit,)).fetchall()

    def get_outbox(self, limit: int = 10):
        with self.connect() as conn:
            return conn.execute("SELECT * FROM outbox ORDER BY sent_at DESC LIMIT ?", (limit,)).fetchall()

    def get_unsent_outbox(self, limit=10):
        with self.connect() as conn:
            return conn.execute(
                "SELECT id, data FROM outbox WHERE delivered = 0 LIMIT ?", (limit,)
            ).fetchall()

    def get_outbox_by_activity_id(self, activity_id: str):
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM outbox WHERE activity_id = ?", (activity_id,)
            ).fetchone()

    def mark_outbox_delivered(self, activity_id: int, error: str = None):
        with self.connect() as conn:
            if error:
                conn.execute(
                    "UPDATE outbox SET delivery_error = ?, delivered = 0 WHERE id = ?",
                    (error, activity_id)
                )
            else:
                conn.execute(
                    "UPDATE outbox SET delivered = 1 WHERE id = ?", (activity_id,)
                )
            conn.commit()

    def get_private_messages_between(self, sender: str, recipient: str):
        with self.connect() as conn:
            inbox_rows = conn.execute("""
                SELECT data FROM inbox
                WHERE json_extract(data, '$.actor') = ?
                  AND json_extract(data, '$.object.to[0]') = ?
            """, (recipient, sender)).fetchall()

            outbox_rows = conn.execute("""
                SELECT data FROM outbox
                WHERE json_extract(data, '$.actor') = ?
                  AND json_extract(data, '$.object.to[0]') = ?
            """, (sender, recipient)).fetchall()

            return inbox_rows + outbox_rows



    def get_users(self):
        with self.connect() as conn:
            return conn.execute("SELECT username FROM users").fetchall()

    def check_user(self, username: str) -> bool:
        with self.connect() as conn:
            result = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
            return result is not None

    def create_user(self, username: str, public_key: str = None, private_key: str = None):
        if self.check_user(username):
            raise ValueError(f"User '{username}' already exists.")
        
        # create PEM keys if not supplied
        if not public_key or not private_key:
            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            private_key = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ).decode("utf-8")
            public_key = key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode("utf-8")

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO keys (user_id, public_key, private_key) VALUES (?, ?, ?)",
                (user_id, public_key, private_key)
            )
            conn.commit()

    def get_keys(self, username: str):
        with self.connect() as conn:
            result = conn.execute("""
                SELECT k.public_key, k.private_key FROM keys k
                JOIN users u ON k.user_id = u.id
                WHERE u.username = ?
            """, (username,)).fetchone()
            return dict(result) if result else None

