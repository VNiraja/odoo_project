# GiftGuard architecture

## Runtime

- **Odoo 18** serves the backend UI, ORM, API controller, and business rules.
- **PostgreSQL 16** stores Odoo data.
- The custom add-on is mounted at `/mnt/extra-addons/custom` and registered in
  `config/odoo.conf`.
- OCA add-ons are optional. GiftGuard currently has no OCA module dependency.

## Add-on responsibilities

`addons/custom/giftguard_compliance` contains the policy, rule, request, and
recipient-organisation models; access controls; XML views; API controller; and
Odoo transaction tests. The manifest declares the add-on's dependencies and
installation data.

## Decision flow

1. An Odoo user or authenticated integration creates a draft request.
2. GiftGuard selects the latest verified policy effective on the current
   Odoo-context date.
3. Rules evaluate amount, currency, category, deal stage, and approved-request
   frequency.
4. A missing/expired policy or ambiguous amount/deal-stage context requires
   human review; a hard-cap or prohibited-category violation is blocked.
5. The policy version, reason, and timestamp are stored on the request. A
   reviewer may approve or reject a review-required request with a note.

Verified policy data and its rules are locked. A policy change should be made
on a copied draft and verified as a new version.

## Local services

`compose.yml` defines PostgreSQL and Odoo services. The `odoo-test` service is
available under the `test` profile and runs Odoo tests in `giftguard_test`.
Database credentials are supplied through an ignored `.env` file and are not
stored in the Odoo config or source tree.
