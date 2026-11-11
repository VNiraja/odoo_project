import json
from odoo import http
from odoo.http import request

class GiftGuardAPI(http.Controller):
    @http.route("/giftguard/v1/evaluate", type="http", auth="public", methods=["POST"], csrf=False)
    def evaluate(self, **kwargs):
        # Demo-only bearer token. Replace with per-integration credentials, hashed storage,
        # rotation, rate limiting and request signing before production.
        expected = request.env["ir.config_parameter"].sudo().get_param("giftguard.api_token")
        auth = request.httprequest.headers.get("Authorization", "")
        if not expected or auth != f"Bearer {expected}":
            return request.make_json_response({"error": "unauthorized"}, status=401)

        try:
            payload = json.loads(request.httprequest.data or b"{}")
            required = ["organisation_id", "recipient_ref", "gift_description", "category", "amount"]
            missing = [key for key in required if key not in payload]
            if missing:
                return request.make_json_response({"error": "missing_fields", "fields": missing}, status=400)

            org = request.env["giftguard.organisation"].sudo().browse(int(payload["organisation_id"])).exists()
            if not org or not org.active:
                return request.make_json_response({"error": "organisation_not_found"}, status=404)

            currency = request.env["res.currency"].sudo().search([("name", "=", payload.get("currency", request.env.company.currency_id.name))], limit=1)
            if not currency:
                return request.make_json_response({"error": "unsupported_currency"}, status=400)

            vals = {
                "organisation_id": org.id,
                "recipient_ref": str(payload["recipient_ref"]),
                "recipient_email": payload.get("recipient_email"),
                "gift_description": str(payload["gift_description"]),
                "category": str(payload["category"]),
                "amount": float(payload["amount"]),
                "currency_id": currency.id,
                "deal_stage": payload.get("deal_stage"),
            }
            rec = request.env["giftguard.request"].sudo().create(vals)
            rec.action_evaluate()
            return request.make_json_response({
                "request_id": rec.name,
                "status": rec.status,
                "reason": rec.decision_reason,
                "policy_version": rec.policy_version,
            }, status=200)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            return request.make_json_response({"error": "invalid_request"}, status=400)
