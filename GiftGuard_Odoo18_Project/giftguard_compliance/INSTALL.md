# Local installation (development only)

1. Use an Odoo 18 development instance with PostgreSQL.
2. Copy `giftguard_compliance/` into a directory included in `addons_path`.
3. Restart Odoo and update the Apps list.
4. Install **GiftGuard Compliance**.
5. Assign a test user to GiftGuard User, and a separate trusted user to GiftGuard Manager / Compliance Reviewer.
6. Create a recipient organisation.
7. Create a policy, add rules, set source/owner/effective/review dates, then click **Mark Verified**.
8. Create a request and click **Evaluate**.

Configure the demo API token in Settings → Technical → System Parameters. The exact menu visibility depends on the Odoo user's technical settings access.

Run tests in an Odoo test database, for example with the Odoo server's `--test-enable` and `--stop-after-init` options and module install/update parameters appropriate to your environment.

## Prototype limitations

- The manifest, XML view compatibility and tests must be verified against the exact Odoo 18 build used by Systema Ops.
- This is a starter implementation, not a production-ready security-reviewed product.
- The API endpoint's shared token + sudo approach is for local demonstration only.
- Recipient-limit counting is a basic prototype and is not concurrency-safe.
- Currency conversion, robust policy version immutability, document parsing, policy-source verification, data retention and multi-company isolation need further work.
