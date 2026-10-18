import os
import unittest
from unittest.mock import patch

from backend.run import main


class BackendRunnerTests(unittest.TestCase):
    def test_runs_selected_backend_on_host_port(self):
        with patch.dict(os.environ, {"B_BACKEND": "neon", "PORT": "10000"}):
            with patch("backend.run.uvicorn.run") as run:
                main()

        run.assert_called_once_with(
            "backend.neonback.main:app",
            host="0.0.0.0",
            port=10000,
        )

    def test_rejects_unknown_backend(self):
        with patch.dict(os.environ, {"B_BACKEND": "unknown"}):
            with self.assertRaisesRegex(SystemExit, "sqlite, supabase, neon"):
                main()


if __name__ == "__main__":
    unittest.main()