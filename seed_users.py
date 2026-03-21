import argparse
import os
import sys

import main as app_main


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed database-backed dashboard users")
    parser.add_argument(
        "--emails",
        nargs="*",
        help="Users to create. Defaults to AUTH_SEED_EMAILS env list.",
    )
    parser.add_argument(
        "--password-env",
        default="AUTH_SEED_DEFAULT_PASSWORD",
        help="Name of the environment variable containing the shared initial password.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    emails = [
        email.strip().lower()
        for email in (args.emails or app_main.AUTH_SEED_EMAILS)
        if email and email.strip()
    ]

    if not emails:
        raise SystemExit(
            "No emails provided. Pass --emails or set the AUTH_SEED_EMAILS environment variable."
        )

    password = os.getenv(args.password_env, "").strip()
    if not password:
        raise SystemExit(
            f"Environment variable '{args.password_env}' is required to seed users safely."
        )

    # initialize_database() calls init_engine() internally, which sets SessionLocal
    app_main.initialize_database()

    if app_main.SessionLocal is None:
        raise SystemExit(
            "Database session factory was not initialized. "
            "Check that DATABASE_URL and JWT_SECRET are set correctly."
        )

    with app_main.SessionLocal() as db:
        try:
            created = app_main.UserService(db).seed_users(emails, password)
        except ValueError as exc:
            raise SystemExit(f"Seeding failed: {exc}") from exc

    if created:
        print(f"Created {len(created)} user(s):")
        for user in created:
            print(f"  - {user.email} ({user.full_name or 'no name'})")
    else:
        print("No new users were created. All requested emails already exist.")


if __name__ == "__main__":
    main()
