"""Run the idempotent Neon schema migration once during deployment."""

from backend.neonback.Database.db import DB


def main() -> None:
    try:
        DB.initialize()
    finally:
        DB.close()


if __name__ == "__main__":
    main()