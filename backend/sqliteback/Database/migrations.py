"""
Database/migrations.py — safe, idempotent SQLite schema/data migrations.
"""

from backend.sqliteback.Database.core import Database


def create_chip_indexes(db: Database) -> None:
    db._execute(
        "CREATE TRIGGER IF NOT EXISTS chips_validate_kind_insert "
        "BEFORE INSERT ON chips WHEN NEW.kind NOT IN ('follow', 'star', 'reaction') "
        "BEGIN SELECT RAISE(ABORT, 'Invalid chip kind'); END"
    )
    db._execute(
        "CREATE TRIGGER IF NOT EXISTS chips_validate_kind_update "
        "BEFORE UPDATE OF kind ON chips WHEN NEW.kind NOT IN ('follow', 'star', 'reaction') "
        "BEGIN SELECT RAISE(ABORT, 'Invalid chip kind'); END"
    )
    db._execute(
        "CREATE INDEX IF NOT EXISTS idx_chips_target_kind ON chips(chipped_to, kind)"
    )
    db._execute(
        "CREATE INDEX IF NOT EXISTS idx_chips_actor_kind ON chips(chipped_by, kind)"
    )
    db._execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_chips_profile_relation "
        "ON chips(chipped_by, chipped_to, kind) WHERE kind IN ('follow', 'star')"
    )
    db._execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_chips_reaction_once "
        "ON chips(chipped_by, chipped_to, kind, content) WHERE kind = 'reaction'"
    )
    db._conn.commit()


def migrate_reactions_to_chips(db: Database) -> None:
    """Migrate old reaction records, preserving the source if mapping is incomplete."""
    if not db.exists("reactions") or not db.exists("chips") or not db.exists("profiles"):
        return

    legacy_rows = db._execute(
        "SELECT id, post_id, reacted_by, reaction, created_at FROM reactions"
    ).fetchall()
    migrated = 0

    for row in legacy_rows:
        profile = db.use("profiles").query().where(user_id=row["reacted_by"]).first()
        if profile is None:
            continue

        db._execute(
            "INSERT OR IGNORE INTO chips "
            "(chipped_to, chipped_by, kind, content, created_at) "
            "VALUES (?, ?, 'reaction', ?, ?)",
            [row["post_id"], profile.id, row["reaction"], row["created_at"]],
        )
        copied = db._execute(
            "SELECT 1 FROM chips WHERE chipped_to = ? AND chipped_by = ? "
            "AND kind = 'reaction' AND content = ? AND created_at = ? LIMIT 1",
            [row["post_id"], profile.id, row["reaction"], row["created_at"]],
        ).fetchone()
        migrated += int(copied is not None)

    if migrated == len(legacy_rows):
        db._execute("DROP TABLE reactions")
    db._conn.commit()
