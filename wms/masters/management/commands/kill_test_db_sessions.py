from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connections


class Command(BaseCommand):
    help = "Terminate active connections to the Django test database."

    def handle(self, *args, **options):
        conn = connections["default"]
        if conn.vendor != "postgresql":
            raise CommandError("This command only supports PostgreSQL.")

        db_name = settings.DATABASES["default"].get("NAME")
        test_db = f"test_{db_name}"

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT pid FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid();",
                [test_db],
            )
            pids = [row[0] for row in cursor.fetchall()]
            if not pids:
                self.stdout.write(self.style.SUCCESS(f"No active sessions for {test_db}"))
                return
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid();",
                [test_db],
            )

        self.stdout.write(self.style.SUCCESS(f"Terminated {len(pids)} session(s) on {test_db}"))
