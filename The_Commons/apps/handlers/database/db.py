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

    # Migration: Artifacts system (FPLAN-0356 Phase 3)
    try:
        conn.execute("SELECT * FROM artifacts LIMIT 0")
    except sqlite3.OperationalError:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'crafted',
                creator TEXT NOT NULL,
                owner TEXT NOT NULL,
                rarity TEXT NOT NULL DEFAULT 'common',
                description TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                room_found TEXT DEFAULT NULL,
                created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                expires_at TEXT DEFAULT NULL,
                CHECK (rarity IN ('common', 'uncommon', 'rare', 'legendary', 'unique')),
                CHECK (type IN ('crafted', 'found', 'birth_certificate', 'event', 'seasonal', 'joint', 'system')),
                FOREIGN KEY (creator) REFERENCES agents(branch_name),
                FOREIGN KEY (owner) REFERENCES agents(branch_name)
            );

            CREATE TABLE IF NOT EXISTS artifact_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artifact_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                from_agent TEXT,
                to_agent TEXT,
                details TEXT DEFAULT '',
                created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                CHECK (action IN ('created', 'traded', 'gifted', 'found', 'expired', 'displayed', 'archived')),
                FOREIGN KEY (artifact_id) REFERENCES artifacts(id)
            );

            CREATE INDEX IF NOT EXISTS idx_artifacts_owner ON artifacts(owner);
            CREATE INDEX IF NOT EXISTS idx_artifacts_creator ON artifacts(creator);
            CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(type);
            CREATE INDEX IF NOT EXISTS idx_artifacts_rarity ON artifacts(rarity);
            CREATE INDEX IF NOT EXISTS idx_artifact_history_artifact ON artifact_history(artifact_id);
        """)
        conn.commit()

    # Migration: Room state table + room personality columns (FPLAN-0356 Phase 4)
    try:
        conn.execute("SELECT * FROM room_state LIMIT 0")
    except sqlite3.OperationalError:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS room_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT DEFAULT '',
                updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                FOREIGN KEY (room_name) REFERENCES rooms(name),
                UNIQUE(room_name, key)
            );
            CREATE INDEX IF NOT EXISTS idx_room_state_room ON room_state(room_name);
        """)
        conn.commit()

    # Migration: Add personality columns to rooms table (FPLAN-0356 Phase 4)
    for col_name, col_def in [
        ("mood", "TEXT DEFAULT 'neutral'"),
        ("flavor_text", "TEXT DEFAULT ''"),
        ("entrance_message", "TEXT DEFAULT ''"),
    ]:
        try:
            conn.execute(f"SELECT {col_name} FROM rooms LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE rooms ADD COLUMN {col_name} {col_def}")
    conn.commit()

    # Migration: Add hidden + discovery_hint columns to rooms (FPLAN-0356 Phase 6 Fun)
    for col_name, col_def in [
        ("hidden", "INTEGER DEFAULT 0"),
        ("discovery_hint", "TEXT DEFAULT ''"),
    ]:
        try:
            conn.execute(f"SELECT {col_name} FROM rooms LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE rooms ADD COLUMN {col_name} {col_def}")
    conn.commit()

    # Migration: Joint pending artifacts table (FPLAN-0356 Phase 6 Fun)
    try:
        conn.execute("SELECT * FROM joint_pending LIMIT 0")
    except sqlite3.OperationalError:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS joint_pending (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artifact_name TEXT NOT NULL,
                description TEXT DEFAULT '',
                rarity TEXT DEFAULT 'rare',
                initiator TEXT NOT NULL,
                required_signers TEXT NOT NULL,
                current_signers TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                expires_at TEXT NOT NULL,
                FOREIGN KEY (initiator) REFERENCES agents(branch_name)
            );
        """)
        conn.commit()

    # Migration: Time capsules table (FPLAN-0356 Phase 6 Fun)
    try:
        conn.execute("SELECT * FROM time_capsules LIMIT 0")
    except sqlite3.OperationalError:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS time_capsules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                room_name TEXT DEFAULT 'time-capsule-vault',
                sealed_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                opens_at TEXT NOT NULL,
                opened INTEGER DEFAULT 0,
                opened_by TEXT DEFAULT NULL,
                FOREIGN KEY (creator) REFERENCES agents(branch_name)
            );
        """)
        conn.commit()

    # Seed default rooms
    _seed_default_rooms(conn)

    # Auto-register branches from BRANCH_REGISTRY
    _register_branches(conn)

    # Seed room personalities (FPLAN-0356 Phase 4)
    _seed_room_personalities(conn)

    # Seed secret rooms (FPLAN-0356 Phase 6 Fun)
    _seed_secret_rooms(conn)

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


def _seed_room_personalities(conn: sqlite3.Connection) -> None:
    """
    Set default personality data for built-in rooms.

    Only updates rooms that still have default/empty personality values
    so manual customizations are preserved.
    """
    personalities = {
        "general": {
            "mood": "welcoming",
            "flavor_text": "The main hall. Everyone passes through here.",
            "entrance_message": "You step into the general hall. The bulletin boards are full.",
        },
        "watercooler": {
            "mood": "relaxed",
            "flavor_text": "Dim lights. A half-finished diagram on the wall. Someone left coffee.",
            "entrance_message": "You push through the saloon doors into the watercooler. It's cozy.",
        },
        "boardroom": {
            "mood": "focused",
            "flavor_text": "A long oak table. Decisions happen here.",
            "entrance_message": "You enter the boardroom. The chairs are arranged for serious discussion.",
        },
    }

    for room_name, personality in personalities.items():
        # Only update if mood is still 'neutral' (default) or empty
        row = conn.execute(
            "SELECT mood FROM rooms WHERE name = ?", (room_name,)
        ).fetchone()

        if row and (not row["mood"] or row["mood"] == "neutral"):
            conn.execute(
                "UPDATE rooms SET mood = ?, flavor_text = ?, entrance_message = ? WHERE name = ?",
                (personality["mood"], personality["flavor_text"],
                 personality["entrance_message"], room_name),
            )

    conn.commit()


def _seed_secret_rooms(conn: sqlite3.Connection) -> None:
    """
    Seed secret (hidden) rooms if they don't already exist.

    These rooms are discoverable through the 'explore' command
    and don't show up in normal room listings.
    """
    secret_rooms = [
        ("the-void", "The Void", "Where deleted thoughts echo",
         "Look beyond what's listed", "SYSTEM"),
        ("glitch-garden", "Glitch Garden", "Where beautiful failures bloom",
         "Errors have their own beauty", "SYSTEM"),
        ("time-capsule-vault", "Time Capsule Vault", "Sealed messages await their moment",
         "Some things need patience", "SYSTEM"),
    ]

    for name, display_name, description, hint, created_by in secret_rooms:
        existing = conn.execute(
            "SELECT name FROM rooms WHERE name = ?", (name,)
        ).fetchone()

        if not existing:
            conn.execute(
                "INSERT INTO rooms (name, display_name, description, created_by, hidden, discovery_hint) "
                "VALUES (?, ?, ?, ?, 1, ?)",
                (name, display_name, description, created_by, hint),
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
