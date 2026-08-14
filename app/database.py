"""Database module using Python's built-in sqlite3 (zero import overhead)."""
import sqlite3
import os
import threading

# Thread-local connections for thread safety
_local = threading.local()
DB_PATH = None


def init_db(app):
    """Initialize the database: create tables if not exist."""
    global DB_PATH
    DB_PATH = os.path.join(app.instance_path, 'app.db')
    os.makedirs(app.instance_path, exist_ok=True)
    conn = get_conn()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            grade TEXT,
            real_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS platform_handles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            platform TEXT NOT NULL,
            handle TEXT NOT NULL,
            UNIQUE(user_id, platform)
        );

        CREATE TABLE IF NOT EXISTS scrape_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            platform TEXT NOT NULL,
            total_solved INTEGER DEFAULT 0,
            rating INTEGER,
            category_stats TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, platform)
        );

        CREATE TABLE IF NOT EXISTS tutorials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            video_url TEXT NOT NULL,
            posted_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS online_contests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            platform TEXT NOT NULL,
            contest_url TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            description TEXT,
            source TEXT DEFAULT 'manual',
            platform_contest_id TEXT,
            posted_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS campus_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            location TEXT,
            event_date DATE,
            registration_deadline TIMESTAMP,
            is_open INTEGER DEFAULT 1,
            posted_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL REFERENCES campus_events(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            contact_phone TEXT,
            contact_email TEXT,
            notes TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS daily_rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            total_solved INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            snapshot_date DATE NOT NULL DEFAULT (date('now')),
            UNIQUE(user_id, snapshot_date)
        );

        CREATE TABLE IF NOT EXISTS awards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            uploaded_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS team_recruitments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            competition_type TEXT NOT NULL,
            recruit_count INTEGER NOT NULL DEFAULT 1,
            requirement TEXT,
            description TEXT,
            wuyu_type TEXT NOT NULL DEFAULT 'zhiyu',
            is_open INTEGER DEFAULT 1,
            posted_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS recruitment_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recruitment_id INTEGER NOT NULL REFERENCES team_recruitments(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(recruitment_id, user_id)
        );

        PRAGMA foreign_keys = ON;
        PRAGMA journal_mode = WAL;
    ''')
    # Migrations for existing databases
    try:
        conn.execute("ALTER TABLE online_contests ADD COLUMN source TEXT DEFAULT 'manual'")
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE online_contests ADD COLUMN platform_contest_id TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE campus_events ADD COLUMN wuyu_type TEXT NOT NULL DEFAULT 'zhiyu'")
    except sqlite3.OperationalError:
        pass  # column already exists
    try:
        conn.execute("ALTER TABLE awards ADD COLUMN wuyu_type TEXT NOT NULL DEFAULT 'zhiyu'")
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.commit()


def get_conn():
    """Get a thread-local database connection."""
    if not hasattr(_local, 'conn') or _local.conn is None:
        _local.conn = sqlite3.connect(DB_PATH)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA foreign_keys = ON")
    return _local.conn


def query(sql, params=(), one=False):
    """Execute a SELECT query. Returns list of dicts, or single dict if one=True."""
    conn = get_conn()
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    if one:
        return dict(rows[0]) if rows else None
    return [dict(r) for r in rows]


def execute(sql, params=()):
    """Execute INSERT/UPDATE/DELETE. Returns lastrowid."""
    conn = get_conn()
    cur = conn.execute(sql, params)
    conn.commit()
    return cur.lastrowid


def close_db():
    """Close the connection (call on app teardown)."""
    if hasattr(_local, 'conn') and _local.conn:
        _local.conn.close()
        _local.conn = None
