# Rugved Job Tracker

This FastAPI app tracks job applications and now supports **multi-user authentication backed by Postgres**.

## Auth environment variables

Keep these Railway variables configured:

- `DATABASE_URL`
- `JWT_SECRET`
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_ADMIN_PASSWORD` or `BOOTSTRAP_ADMIN_PASSWORD_HASH`

Legacy `DASHBOARD_EMAIL`, `DASHBOARD_PASSWORD`, and `DASHBOARD_PASSWORD_HASH` still work as fallback bootstrap values so existing Railway deployments can upgrade safely.

## How auth bootstrapping works

- On startup, the app creates the `users` table if it does not exist.
- If the table is empty, it creates the first admin user from the bootstrap env vars above.
- JWT cookie auth and the current frontend login flow remain unchanged.

## Seed the default users safely

Set a temporary shared password in an environment variable, then run:

```bash
AUTH_SEED_DEFAULT_PASSWORD='set-a-temp-password' python seed_users.py \
  --emails rugved261@gmail.com akanshac0204@gmail.com
```

You can also rely on `AUTH_SEED_EMAILS` and just run:

```bash
AUTH_SEED_DEFAULT_PASSWORD='set-a-temp-password' python seed_users.py
```

After the users sign in, rotate passwords through your preferred admin workflow or by updating their stored hashes in Postgres.
