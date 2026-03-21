import argparse
import os

import main as app_main


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed database-backed dashboard users")
    parser.add_argument("--emails", nargs="*", help="Users to create. Defaults to AUTH_SEED_EMAILS env list.")
    parser.add_argument(
        "--password-env",
        default="AUTH_SEED_DEFAULT_PASSWORD",
        help="Name of the environment variable containing the shared initial password.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    emails = [email.strip().lower() for email in (args.emails or app_main.AUTH_SEED_EMAILS) if email and email.strip()]
    password = os.getenv(args.password_env, "")
    if not password:
        raise SystemExit(f"Environment variable {args.password_env} is required to seed users safely.")
    app_main.initialize_database()
    with app_main.SessionLocal() as db:
        created = app_main.UserService(db).seed_users(emails, password)
    if created:
        print("Created users:")
        for user in created:
            print(f"- {user.email}")
    else:
        print("No users were created. All requested emails already exist.")


if __name__ == "__main__":
    main()
