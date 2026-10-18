import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit
from unittest.mock import sentinel

from backend.sqliteback.config import DB_POOL_MAX_SIZE, DB_POOL_MAX_WAITING
from backend.supaback.Database.db import (
    PostgresDatabase,
    SCHEMA_SQL,
    _cast_timestamp_parameters,
    _encode_postgres_credentials,
)


class PostgresAdapterTests(unittest.TestCase):
    def test_pool_uses_configured_hard_connection_limit(self):
        database = PostgresDatabase("postgresql://postgres:secret@pooler.example/postgres")
        with patch("psycopg_pool.ConnectionPool") as pool_class:
            pool_class.return_value.getconn.return_value = sentinel.connection
            self.assertIs(database._require_connection(), sentinel.connection)

        options = pool_class.call_args.kwargs
        self.assertEqual(options["max_size"], DB_POOL_MAX_SIZE)
        self.assertEqual(options["max_waiting"], DB_POOL_MAX_WAITING)
        self.assertFalse(options["open"])
        pool_class.return_value.open.assert_called_once()

    def test_database_uri_credentials_are_encoded_once(self):
        raw_uri = "postgresql://postgres:pa@ss:/?#@pooler.example:5432/postgres?sslmode=require"
        encoded_uri = _encode_postgres_credentials(raw_uri)
        parsed = urlsplit(encoded_uri)
        self.assertEqual(parsed.hostname, "pooler.example")
        self.assertEqual(unquote(parsed.password or ""), "pa@ss:/?#")
        self.assertEqual(
            _encode_postgres_credentials(encoded_uri),
            encoded_uri,
        )

    def test_rejects_supabase_project_api_url_as_database_url(self):
        database = PostgresDatabase("https://project.supabase.co")
        with self.assertRaisesRegex(RuntimeError, "PostgreSQL connection URI"):
            database._require_connection()

    def test_database_url_is_resolved_after_adapter_creation(self):
        database = PostgresDatabase()
        with patch.dict(
            "os.environ",
            {
                "B_SUPABASE_DB_URL": "postgresql://postgres.[project]:[{pass}]@pooler.example/postgres",
                "B_SUPABASE_DB_PASS": "p@ss:/?#",
            },
        ):
            self.assertEqual(
                database._resolve_database_url(),
                "postgresql://postgres.[project]:p%40ss%3A%2F%3F%23@pooler.example/postgres",
            )

    def test_database_url_placeholder_requires_db_pass(self):
        database = PostgresDatabase()
        with patch.dict("os.environ", {"B_SUPABASE_DB_URL": "postgresql://postgres:{pass}@host/db"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "B_SUPABASE_DB_PASS is required"):
                database._resolve_database_url()

    def test_schema_bootstrap_includes_all_application_tables(self):
        table_statements = [
            statement.strip().split()[5]
            for statement in SCHEMA_SQL
            if statement.lstrip().upper().startswith("CREATE TABLE IF NOT EXISTS")
        ]
        self.assertEqual(
            set(table_statements),
            {"users", "sessions", "profiles", "posts", "chips", "notifications"},
        )
        rls_statements = {
            statement
            for statement in SCHEMA_SQL
            if statement.startswith("ALTER TABLE") and "ENABLE ROW LEVEL SECURITY" in statement
        }
        self.assertEqual(
            rls_statements,
            {
                f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"
                for table in table_statements
            },
        )

    def test_timestamp_values_are_cast_for_insert_update_and_filter(self):
        insert_sql = (
            'INSERT INTO "sessions" ("token", "expires_at") '
            'VALUES (%s, %s)'
        )
        update_sql = 'UPDATE "sessions" SET "expires_at" = %s WHERE "id" = %s'
        filter_sql = 'SELECT * FROM "sessions" WHERE "expires_at" < %s'

        self.assertIn("VALUES (%s, %s::timestamp)", _cast_timestamp_parameters(insert_sql))
        self.assertIn('"expires_at" = %s::timestamp', _cast_timestamp_parameters(update_sql))
        self.assertIn('"expires_at" < %s::timestamp', _cast_timestamp_parameters(filter_sql))


if __name__ == "__main__":
    unittest.main()