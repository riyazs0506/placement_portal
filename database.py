"""
database.py — SQLAlchemy engine, session, auto-migrations.
Works with MySQL (production/Aiven) and SQLite (local Windows dev).
Auto-migrates: adds any missing columns on every startup without losing data.
"""
import os, logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./placement_portal.db")
IS_MYSQL     = "mysql" in DATABASE_URL

# ── Engine ──────────────────────────────────────────────────────────
if IS_MYSQL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=20, max_overflow=40,
        pool_timeout=30, pool_recycle=1800,
        pool_pre_ping=True, echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Migration helpers ────────────────────────────────────────────────

def _table_exists(conn, table: str) -> bool:
    if IS_MYSQL:
        r = conn.execute(text("SHOW TABLES LIKE :t"), {"t": table})
    else:
        r = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
            {"t": table})
    return r.fetchone() is not None


def _column_exists(conn, table: str, column: str) -> bool:
<<<<<<< HEAD
    try:
        if IS_MYSQL:
            r = conn.execute(
                text("""SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_SCHEMA=DATABASE()
                        AND TABLE_NAME=:t AND COLUMN_NAME=:c"""),
                {"t": table, "c": column})
            return r.fetchone() is not None
        else:
            r = conn.execute(text(f"PRAGMA table_info(`{table}`)"))
            return any(row[1] == column for row in r.fetchall())
    except Exception:
        return False


def _add_column(conn, table: str, column: str, mysql_def: str, sqlite_def: str):
    """Safely add a column if it doesn't exist yet."""
    if not _table_exists(conn, table):
        return  # table will be created by create_all()
    if _column_exists(conn, table, column):
        return  # already exists
    col_def = mysql_def if IS_MYSQL else sqlite_def
    try:
        if IS_MYSQL:
            conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {col_def}"))
        else:
            conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {col_def}'))
        conn.commit()
        logger.info(f"✅ Migration: {table}.{column} added")
    except Exception as e:
        logger.warning(f"Migration skip {table}.{column}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
=======
    """Check if a column exists in a table (SQLite or MySQL)."""
    if DATABASE_URL.startswith("sqlite"):
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        return any(row[1] == column for row in result.fetchall())
    else:
        result = conn.execute(
            text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = :t
                AND COLUMN_NAME = :c
            """),
            {"t": table, "c": column}
        )
        return result.fetchone() is not None
>>>>>>> af4f32748063e99991af38a663e1b62643a31674


def migrate_db():
    """
    Add every column that exists in models.py but might be missing from
    an old database. Safe to run repeatedly — skips already-present columns.

    Format: (table, column, mysql_definition, sqlite_definition)
    """
    ALL_MIGRATIONS = [
        # ── users: core fields (v2.1) ────────────────────────────────
        ("users", "phone",               "VARCHAR(20) NULL",         "VARCHAR(20)"),
        ("users", "company_designation", "VARCHAR(200) NULL",        "VARCHAR(200)"),
        ("users", "tenth_percent",       "FLOAT NULL",               "REAL"),
        ("users", "twelfth_percent",     "FLOAT NULL",               "REAL"),
        ("users", "backlogs",            "INT NOT NULL DEFAULT 0",   "INTEGER DEFAULT 0"),
        ("users", "batch_year",          "INT NULL",                 "INTEGER"),
        ("users", "roll_number",         "VARCHAR(50) NULL",         "VARCHAR(50)"),

        # ── users: profile fields (v2.3) ─────────────────────────────
        ("users", "address",             "TEXT NULL",                "TEXT"),
        ("users", "bio",                 "TEXT NULL",                "TEXT"),
        ("users", "linkedin_url",        "VARCHAR(500) NULL",        "VARCHAR(500)"),
        ("users", "github_url",          "VARCHAR(500) NULL",        "VARCHAR(500)"),
        ("users", "portfolio_url",       "VARCHAR(500) NULL",        "VARCHAR(500)"),
        ("users", "resume_url",          "VARCHAR(500) NULL",        "VARCHAR(500)"),
        ("users", "skills",              "JSON NULL",                "TEXT"),
        ("users", "languages",           "JSON NULL",                "TEXT"),
        ("users", "certifications",      "JSON NULL",                "TEXT"),
        ("users", "projects",            "JSON NULL",                "TEXT"),
        ("users", "profile_complete",    "TINYINT(1) NOT NULL DEFAULT 0", "INTEGER DEFAULT 0"),

        # ── notifications (v2.1) ─────────────────────────────────────
        ("notifications", "target_user_id", "INT NULL",             "INTEGER"),

        # ── drive_round_results (v2.1) ────────────────────────────────
        ("drive_round_results", "notified", "TINYINT(1) NOT NULL DEFAULT 0", "INTEGER DEFAULT 0"),

        # ── campus_drives: drive type (v2.3) ─────────────────────────
        ("campus_drives", "drive_type",
         "VARCHAR(20) NOT NULL DEFAULT 'recruitment'",
         "VARCHAR(20) DEFAULT 'recruitment'"),
        ("campus_drives", "stipend_amount",       "FLOAT NULL",      "REAL"),
        ("campus_drives", "internship_duration",  "VARCHAR(100) NULL","VARCHAR(100)"),
        ("campus_drives", "planned_rounds",       "JSON NULL",       "TEXT"),
    ]

    with engine.connect() as conn:
<<<<<<< HEAD
        for table, column, mysql_def, sqlite_def in ALL_MIGRATIONS:
            _add_column(conn, table, column, mysql_def, sqlite_def)
=======
        for table, column, col_type, default in migrations:
            # Check table exists first
            if DATABASE_URL.startswith("sqlite"):
                tables = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name=:t"),
                    {"t": table}
                ).fetchall()
            else:
                tables = conn.execute(
                    text("SHOW TABLES LIKE :t"),
                    {"t": table}
                ).fetchall()
            if not tables:
                continue  # Table doesn't exist yet; create_tables will make it

            if not _column_exists(conn, table, column):
                try:
                    conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default}"
                    ))
                    conn.commit()
                    logger.info(f"✅ Migration: added {table}.{column}")
                except Exception as e:
                    logger.warning(f"Migration warning for {table}.{column}: {e}")
>>>>>>> af4f32748063e99991af38a663e1b62643a31674


def create_tables():
    """
    1. Create all tables that don't exist yet (from models.py).
    2. Run column migrations to add any missing columns to existing tables.
    """
    Base.metadata.create_all(bind=engine)
    migrate_db()
<<<<<<< HEAD
    logger.info("✅ Database ready")
=======
>>>>>>> af4f32748063e99991af38a663e1b62643a31674
