# Security notes

This repository is configured for local development, not production deployment.

- Replace all `.env.example` values in `.env`; `.env` is ignored by Git.
- The Odoo HTTP port is bound to localhost by default.
- The API currently uses a shared demonstration token and `sudo()`; do not
  expose it to untrusted networks.
- Company record rules limit interactive access to the user's allowed
  companies. The API also checks the organisation's company before creating a
  request.
- Requests do not store recipient home addresses.
- Review retention, privacy, integration authentication, rate limiting,
  backups, TLS, and secret rotation before any pilot.
