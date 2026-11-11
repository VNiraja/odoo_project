# API example

Configure a demo token in Odoo System Parameters:
- Key: `giftguard.api_token`
- Value: use a long random secret for local testing only.

POST `/giftguard/v1/evaluate`

Headers:
`Authorization: Bearer <token>`
`Content-Type: application/json`

Example body:
```json
{
  "organisation_id": 1,
  "recipient_ref": "crm-contact-ref-123",
  "recipient_email": "recipient@example.org",
  "gift_description": "Branded notebook set",
  "category": "stationery",
  "amount": 2500,
  "currency": "INR",
  "deal_stage": "negotiation"
}
```

Possible response:
```json
{
  "request_id": "GG/2026/00001",
  "status": "approved",
  "reason": "All configured rules passed.",
  "policy_version": 1
}
```

This API uses a single demo token and `sudo()` for the prototype. Do not expose it publicly or use it for production. Implement per-client credentials, token hashing/rotation, rate limits, idempotency keys, strict payload validation, audit of API callers and security review before any pilot.
