import hmac
import json
import math

from odoo import http
from odoo.http import request


class GiftGuardAPI(http.Controller):
    @http.route("/giftguard/v1/evaluate", type="http", auth="public", methods=["POST"], csrf=False)
    def evaluate(self, **kwargs):
        # Demo-only bearer token. Replace with per-integration credentials, hashed storage,
        # rotation, rate limiting and request signing before production.
        expected = request.env["ir.config_parameter"].sudo().get_param("giftguard.api_token")
        auth = request.httprequest.headers.get("Authorization", "")
        if not expected or not hmac.compare_digest(auth, f"Bearer {expected}"):
            return request.make_json_response({"error": "unauthorized"}, status=401)

        try:
            payload = json.loads(request.httprequest.data or b"{}")
            if not isinstance(payload, dict):
                return request.make_json_response({"error": "invalid_request"}, status=400)

            required = ["organisation_id", "recipient_ref", "gift_description", "category", "amount"]
            missing = [key for key in required if key not in payload]
            if missing:
                return request.make_json_response({"error": "missing_fields", "fields": missing}, status=400)

            organisation_id = payload["organisation_id"]
            if (
                isinstance(organisation_id, bool)
                or not isinstance(organisation_id, int)
                or organisation_id <= 0
            ):
                return request.make_json_response({"error": "invalid_organisation_id"}, status=400)

            amount = payload["amount"]
            if isinstance(amount, bool) or not isinstance(amount, (int, float)):
                return request.make_json_response({"error": "invalid_amount"}, status=400)
            try:
                amount = float(amount)
            except (OverflowError, ValueError):
                return request.make_json_response({"error": "invalid_amount"}, status=400)
            if not math.isfinite(amount) or amount < 0:
                return request.make_json_response({"error": "invalid_amount"}, status=400)

            string_fields = ("recipient_ref", "gift_description", "category")
            if any(
                not isinstance(payload[field], str) or not payload[field].strip()
                for field in string_fields
            ):
                return request.make_json_response({"error": "invalid_request"}, status=400)
            for field in ("recipient_email", "deal_stage"):
                if payload.get(field) is not None and not isinstance(payload[field], str):
                    return request.make_json_response({"error": "invalid_request"}, status=400)

            org = request.env["giftguard.organisation"].sudo().browse(organisation_id).exists()
            if not org or not org.active:
                return request.make_json_response({"error": "organisation_not_found"}, status=404)
            if org.company_id not in request.env.companies:
                return request.make_json_response({"error": "organisation_not_found"}, status=404)

            currency_name = payload.get("currency", org.company_id.currency_id.name)
            if not isinstance(currency_name, str) or not currency_name.strip():
                return request.make_json_response({"error": "unsupported_currency"}, status=400)
            currency = request.env["res.currency"].sudo().search(
                [("name", "=", currency_name.strip().upper())],
                limit=1,
            )
            if not currency:
                return request.make_json_response({"error": "unsupported_currency"}, status=400)

            vals = {
                "organisation_id": org.id,
                "recipient_ref": payload["recipient_ref"].strip(),
                "recipient_email": (payload.get("recipient_email") or "").strip() or False,
                "gift_description": payload["gift_description"].strip(),
                "category": payload["category"].strip(),
                "amount": amount,
                "currency_id": currency.id,
                "deal_stage": (payload.get("deal_stage") or "").strip() or False,
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
