# GiftGuard Odoo 18

GiftGuard is an Odoo 18 add-on for checking corporate gift requests against
organisation-authorised policies. It records an explainable decision and sends
exceptions to a compliance reviewer. It is a prototype, not legal advice or a
compliance certification.

## Project layout

```text
GiftGuard_Odoo18_Project/
├── addons/
│   ├── custom/
│   │   └── giftguard_compliance/
│   └── oca/
├── config/
│   └── odoo.conf
├── docs/
├── scripts/
├── tools/
├── Dockerfile
└── compose.yml
```

## Start the local development stack

Requirements: Docker Desktop with Docker Compose.

1. Copy `.env.example` to `.env` and replace both development passwords.
2. From this directory, run `docker compose up --build -d`.
3. Open `http://localhost:8069` and create a database named `giftguard`.
   Use `ODOO_MASTER_PASSWORD` from `.env` as the master password.
4. Update the Apps list and install **GiftGuard Compliance**.

View logs with `docker compose logs -f odoo`; stop the stack with
`docker compose down`. The named PostgreSQL and Odoo volumes are retained.
Use `docker compose down -v` only when you intentionally want to erase local
database and Odoo data.

The database and application ports are for local development. Do not reuse the
sample passwords or expose this stack publicly.

## Validate and test

Run the dependency-free structural checks:

```powershell
python tools/validate_addon.py
```

Run Odoo's module tests in the Docker stack:

```powershell
Copy-Item .env.example .env
# Set real local-only values in .env before continuing.
docker compose --profile test run --rm odoo-test
```

The test service installs `giftguard_compliance` into a separate
`giftguard_test` database and exits after the test run.

## Documentation

- [Development and module installation](docs/DEVELOPMENT.md)
- [Architecture and data flow](docs/ARCHITECTURE.md)
- [Security and deployment limitations](docs/SECURITY.md)
- [Add-on README](addons/custom/giftguard_compliance/README.md)
- [Add-on installation steps](addons/custom/giftguard_compliance/INSTALL.md)
