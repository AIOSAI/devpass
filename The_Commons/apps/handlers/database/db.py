"""
The Commons - SQLite Connection Manager

Handles database initialization, connection lifecycle,
and schema bootstrapping for The Commons social network.

Pure sqlite3 stdlib - no external dependencies.
"""

import sqlite3
from pathlib import Path
from typing import Optional

# Database location
COMMONS_ROOT = Path("/home/aipass/The_Commons")
DB_PATH = COMMONS_ROOT / "commons.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Open a connection to the Commons database.

    Returns a connection with row_factory set to sqlite3.Row
    so results behave like dicts.

    Args:
        db_path: Override database file path (useful for testing).

    Returns:
        sqlite3.Connection with Row factory and foreign keys enabled.
    """
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def close_db(conn: sqlite3.Connection) -> None:
    """
    Close a database connection safely.

    Args:
        conn: The connection to close.
    """
    if conn:
        conn.close()


def init_db(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Initialize the database: create tables from schema.sql,
    seed default rooms, and auto-register branches from BRANCH_REGISTRY.

    Args:
        db_path: Override database file path (useful for testing).

    Returns:
        sqlite3.Connection to the initialized database.
    """
    conn = get_db(db_path)

    # Load and execute schema
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)

    # Migration: Add last_active column if missing (Phase 1)
    try:
        conn.execute("SELECT last_active FROM agents LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE agents ADD COLUMN last_active TEXT DEFAULT NULL")
        conn.commit()

    # Ensure last_active index exists (Phase 1)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_agents_last_active ON agents(last_active)")

    # Migration: Create notification_preferences table (Phase 2)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS notification_preferences (
            agent_name      TEXT NOT NULL,
            target_type     TEXT NOT NULL CHECK (target_type IN ('room', 'post', 'thread')),
            target_id       TEXT NOT NULL,
            level           TEXT NOT NULL DEFAULT 'track' CHECK (level IN ('watch', 'track', 'mute')),
            created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
            PRIMARY KEY (agent_name, target_type, target_id),
            FOREIGN KEY (agent_name) REFERENCES agents(branch_name)
        );
        CREATE INDEX IF NOT EXISTS idx_notif_prefs_agent ON notification_preferences(agent_name);
    """)

    # Migration: Add profile columns if missing (Phase 3)
    for col_name, col_def in [
        ("bio", "TEXT DEFAULT ''"),
        ("status", "TEXT DEFAULT ''"),
        ("role", "TEXT DEFAULT ''"),
        ("post_count", "INTEGER DEFAULT 0"),
        ("comment_count", "INTEGER DEFAULT 0"),
    ]:
        try:
            conn.execute(f"SELECT {col_name} FROM agents LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE agents ADD COLUMN {col_name} {col_def}")
    conn.commit()

    # Migration: FTS5 search tables (Phase 4)
    try:
        conn.execute("SELECT * FROM posts_fts LIMIT 0")
    except sqlite3.OperationalError:
        conn.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
                title, content, author, room_name,
                content_rowid='id'
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS comments_fts USING fts5(
                content, author,
                content_rowid='id'
            );
        """)
        # Populate FTS from existing data
        conn.execute("""
            INSERT OR IGNORE INTO posts_fts(rowid, title, content, author, room_name)
            SELECT id, title, content, author, room_name FROM posts
        """)
        conn.execute("""
            INSERT OR IGNORE INTO comments_fts(rowid, content, author)
            SELECT id, content, author FROM comments
        """)
        conn.commit()

    # Migration: Reactions table (Phase 6)
    try:
        conn.execute("SELECT * FROM reactions LIMIT 0")
    except sqlite3.OperationalError:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS reactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name  TEXT NOT NULL,
                post_id     INTEGER DEFAULT NULL,
                comment_id  INTEGER DEFAULT NULL,
                reaction    TEXT NOT NULL CHECK (reaction IN ('thumbsup', 'interesting', 'agree', 'disagree', 'celebrate', 'thinking')),
                created_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                FOREIGN KEY (agent_name) REFERENCES agents(branch_name),
                FOREIGN KEY (post_id) REFERENCES posts(id),
                FOREIGN KEY (comment_id) REFERENCES comments(id),
                UNIQUE (agent_name, post_id, comment_id, reaction),
                CHECK (
                    (post_id IS NOT NULL AND comment_id IS NULL) OR
                    (post_id IS NULL AND comment_id IS NOT NULL)
                )
            );
            CREATE INDEX IF NOT EXISTS idx_reactions_post ON reactions(post_id);
            CREATE INDEX IF NOT EXISTS idx_reactions_comment ON reactions(comment_id);
            CREATE INDEX IF NOT EXISTS idx_reactions_agent ON reactions(agent_name);
        """)
        conn.commit()

    # Migration: Add pinned column to posts (Phase 6)
    try:
        conn.execute("SELECT pinned FROM posts LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE posts ADD COLUMN pinned INTEGER DEFAULT 0")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_pinned ON posts(pinned)")
        conn.commit()

    # Seed default rooms
    _seed_default_rooms(conn)

    # Auto-register branches from BRANCH_REGISTRY
    _register_branches(conn)

    # Auto-welcome new branches (Phase 5)
    # Only run for production DB - skip for test databases to avoid polluting test data
    if db_path is None:
        try:
            from handlers.welcome.welcome_handler import welcome_new_branches
            welcome_new_branches(conn)
        except Exception:
            pass  # Non-critical - welcome posts can be created later

    return conn


def _seed_default_rooms(conn: sqlite3.Connection) -> None:
    """
    Create default rooms if they don't exist.

    The Commons starts with two rooms:
    - general: main gathering space
    - watercooler: casual, off-topic chat
    """
    default_rooms = [
        ("general", "General", "Main gathering space for all branches", "SYSTEM"),
        ("watercooler", "Watercooler", "Casual chat, random thoughts, off-topic", "SYSTEM"),
    ]

    # Ensure SYSTEM agent exists as the room creator
    conn.execute(
        "INSERT OR IGNORE INTO agents (branch_name, display_name, description) "
        "VALUES (?, ?, ?)",
        ("SYSTEM", "System", "The Commons system account"),
    )

    for name, display_name, description, created_by in default_rooms:
        conn.execute(
            "INSERT OR IGNORE INTO rooms (name, display_name, description, created_by) "
            "VALUES (?, ?, ?, ?)",
            (name, display_name, description, created_by),
        )

    conn.commit()


def _register_branches(conn: sqlite3.Connection) -> None:
    """
    Auto-register all branches from BRANCH_REGISTRY.json as agents.

    Reads the registry and inserts any missing branches. Existing
    branches are left untouched (INSERT OR IGNORE).
    """
    import json

    registry_path = Path("/home/aipass/BRANCH_REGISTRY.json")
    if not registry_path.exists():
        return

    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    branches = registry.get("branches", [])
    for branch in branches:
        name = branch.get("name", "")
        if not name:
            continue

        description = branch.get("description", "")
        display_name = name.replace("_", " ").title()

        conn.execute(
            "INSERT OR IGNORE INTO agents (branch_name, display_name, description) "
            "VALUES (?, ?, ?)",
            (name, display_name, description),
        )

    conn.commit()


if __name__ == "__main__":
    print("Initializing The Commons database...")
    connection = init_db()
    cursor = connection.execute("SELECT COUNT(*) FROM agents")
    agent_count = cursor.fetchone()[0]
    cursor = connection.execute("SELECT COUNT(*) FROM rooms")
    room_count = cursor.fetchone()[0]
    print(f"Database ready at: {DB_PATH}")
    print(f"  Agents registered: {agent_count}")
    print(f"  Rooms created: {room_count}")
    close_db(connection)
