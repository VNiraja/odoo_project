{
    "name": "GiftGuard Compliance",
    "version": "18.0.1.0.1",
    "category": "Services",
    "summary": "Organisation-authorised corporate gifting policy checks",
    "description": """
GiftGuard evaluates gifting requests against organisation-authorised policies,
records explainable decisions, and routes exceptions for compliance review.
This module is a prototype and does not provide legal or compliance certification.
    """,
    "author": "Systema Ops",
    "depends": ["base", "mail"],
    "data": [
        "security/giftguard_security.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/organisation_views.xml",
        "views/policy_views.xml",
        "views/request_views.xml",
        "views/menu_views.xml",
    ],
    "application": True,
    "auto_install": False,
    "installable": True,
    "license": "LGPL-3",
}
