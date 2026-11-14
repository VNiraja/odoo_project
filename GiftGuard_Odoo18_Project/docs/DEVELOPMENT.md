# Development guide

## Set up the environment

1. Install Docker Desktop with Compose support.
2. Copy `.env.example` to `.env` and set unique local PostgreSQL and Odoo master
   passwords.
3. Start the services with `docker compose up --build -d`.
4. Create an Odoo database named `giftguard` at `http://localhost:8069`, using
   the Odoo master password from `.env`.
5. Update the Apps list and install **GiftGuard Compliance**.

The `addons/custom` directory is bind-mounted, so add-on source edits appear in
the container. Restart Odoo after changing Python files.

## Run checks

`python tools/validate_addon.py` checks Python syntax, XML well-formedness,
manifest data paths, and ACL model references without requiring Odoo.

`docker compose --profile test run --rm odoo-test` installs the module into the
separate `giftguard_test` database and runs its Odoo `TransactionCase` tests.

## Operational details

- The extension uses only Odoo core (`base` and `mail`); no OCA modules are
  required.
- Database data is stored in named Docker volumes.
- Recipient limits count approved requests, not confirmed deliveries, and
  are not concurrency-safe in this prototype.
- Currency conversion, production-grade integration credentials, idempotency,
  rate limiting, and policy source verification remain out of scope.
