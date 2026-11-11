{
    "name": "GiftGuard Compliance",
    "version": "18.0.1.0.0",
    "category": "Sales",
    "summary": "Organisation-authorised corporate gifting policy checks",
    "description": "A research MVP for gift policy registry, deterministic checks and audit decisions.",
    "depends": ["base", "mail", "contacts"],
    "data": [
        "data/sequence.xml",
        "security/giftguard_security.xml",
        "security/ir.model.access.csv",
        "views/organisation_views.xml",
        "views/policy_views.xml",
        "views/request_views.xml",
        "views/menu_views.xml"
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
