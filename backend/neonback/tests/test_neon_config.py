import unittest
from unittest.mock import patch

from backend.neonback.Database.db import DB


class NeonConfigTests(unittest.TestCase):
    def test_neon_uses_neon_specific_credentials(self):
        self.assertEqual(DB.database_url_env, "B_NEON_DB_URL")
        self.assertEqual(DB.password_env, "B_NEON_DB_PASS")
        self.assertEqual(DB.provider_name, "Neon")

    def test_neon_url_password_is_resolved_independently(self):
        with patch.dict(
            "os.environ",
            {
                "B_NEON_DB_URL": "postgresql://user:{pass}@neon.example/db",
                "B_NEON_DB_PASS": "neon-password",
                "B_SUPABASE_DB_URL": "postgresql://other@supabase.example/db",
                "B_SUPABASE_DB_PASS": "supabase-password",
            },
        ):
            self.assertEqual(
                DB._resolve_database_url(),
                "postgresql://user:neon-password@neon.example/db",
            )


if __name__ == "__main__":
    unittest.main()