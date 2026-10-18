"""Run the idempotent Supabase schema migration once during deployment."""

from backend.supaback.Database.db import DB


def main() -> None:
    try:
        DB.initialize()
    finally:
        DB.close()


if __name__ == "__main__":
    main()