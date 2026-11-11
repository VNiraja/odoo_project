# GiftGuard — Odoo 18 Corporate Gifting Compliance Add-on

**Prepared as a Systema Ops product-discovery and MVP proposal.**  
**Status:** Prototype scaffold / research hypothesis — not production-ready and not evidence of a validated market gap.

## 1. Executive summary

GiftGuard is a proposed API-first compliance add-on for corporate gifting workflows. It is intended to sit inside an existing ERP/CRM (initially Odoo 18), rather than ask a customer to replace its current gifting platform.

A sender or connected application submits a gifting request. GiftGuard evaluates the request against policy rules that the recipient organisation has explicitly supplied or authorised the system to use. It returns `approved`, `blocked`, or `review_required`, with a reason and an audit record.

### Important market finding

Do **not** claim that address privacy or gift-policy controls are entirely unsolved:

- Sendoso advertises SmartDelivery, where a sender can send using a recipient's name and email without first knowing their address; it describes address discovery and recipient address-confirmation fallback. Sendoso also advertises Policy Center controls, including recipient limits and Salesforce-integrated policies.
- Reachdesk advertises Address Confirmation, allowing a recipient to choose where to receive a gift without the sender having the address.
- OCA's Odoo 18 `sale_stock_delivery_address` supports a different delivery address per sales order line and can split deliveries. It is not a gifting-compliance engine.

**Potential differentiator to validate:** a vendor-neutral, recipient-organisation policy verification service that can be embedded into several ERPs/CRMs/gifting tools, provided the recipient organisation supplies or authorises access to its current rules. Public evidence reviewed does not establish whether Sendoso/Reachdesk retrieve and enforce the recipient's *employer's own* anti-bribery/gift-acceptance policy. That exact distinction requires interviews and product demos.

Never market this as “unique” or “not done by anyone” until competitor testing and customer validation are complete.

## 2. Problem statement

When one company sends a gift to an employee of another company, the sender may know its own internal gifting policy but not the recipient organisation's rules. The gift may be prohibited, exceed a threshold, require pre-approval, or be restricted during procurement/contract negotiations.

A second, related issue is delivery privacy: the sender may not need to see or store the recipient's personal home address.

### What is known vs what is still a hypothesis

| Statement | Current assessment |
|---|---|
| Gift senders need controls over gift value and recipient frequency | Existing platforms advertise policy controls; not a new claim |
| Recipients may prefer not to disclose a home address to the sender | Existing address-confirmation / address-discovery features address parts of this |
| Every employer has a machine-readable gift policy | **Unproven**; many policies may be unavailable, private, or context-dependent |
| A cross-company service can reliably retrieve recipient employer policies | **Unproven and the biggest feasibility risk** |
| Companies will pay for a neutral compliance API | **Unvalidated commercial hypothesis** |
| A policy engine embedded in Odoo/CRM can reduce manual checks | Plausible; validate with real customer workflow data |

## 3. Proposed modules to build

Build the smallest useful product first. Do not build a new marketplace, courier network, or complete gifting ERP.

| Module | What it does | Why build it | Existing coverage / gap assessment |
|---|---|---|---|
| 1. Organisation Policy Registry | Stores recipient organisation's approved policy, source, owner, effective date, review date and status | Provides a controlled source of truth | Generic policy storage exists in many systems. GiftGuard's recipient-company policy schema is a proposed domain model; uniqueness unproven |
| 2. Gift Rule Engine | Checks max value, currency, prohibited categories, approval thresholds, deal-stage restrictions and recipient frequency | Stops obviously non-compliant requests before dispatch | Sendoso Policy Center advertises sending policies and recipient limits. Need test whether it enforces *recipient employer* rules, not just sender-account rules |
| 3. Compliance Decision & Audit | Returns approved / blocked / review-required with reasons; records policy version and decision timestamp | Makes decisions explainable and reviewable | Approval/audit functions are common; recipient-policy-aware cross-platform implementation is the hypothesis |
| 4. Approval Workflow | Routes exceptions to an authorised reviewer; records decision, comments and timestamp | Some rules need human interpretation | Existing ERP approval workflows can cover much of this; custom code only for GiftGuard-specific links |
| 5. ERP/CRM Integration API | Receives requests and returns decisions to Odoo or another authorised system | Lets customers keep their existing ERP/CRM | APIs are common. Product value depends on stable connectors and a useful policy service |
| 6. Privacy-Minimised Recipient Handoff (later phase) | Uses a one-time recipient token or approved corporate delivery point; sender cannot read the private address | Reduces unnecessary address exposure | Sendoso and Reachdesk already address recipient address confirmation/privacy. Do not rebuild their feature; integrate with a fulfilment provider or implement only a validated gap |

### MVP scope (recommended)

Implement modules 1–5 in Odoo 18. Keep module 6 as a later integration, not a promise in the first demo.

**MVP features**
- Create recipient organisations and policy records.
- Add rules for maximum gift value, prohibited categories, approval threshold, deal-stage restrictions and recipient limits.
- Submit a gifting request from Odoo form or JSON API.
- Return `approved`, `blocked`, or `review_required`.
- Log the exact policy version and reason for each decision.
- Allow a compliance reviewer to approve/reject a review-required request.
- Provide access groups and avoid storing home addresses in the MVP.

**Explicitly out of scope**
- Automatically scraping confidential corporate policies.
- Claiming legal compliance certification.
- Automatically changing a gift to a cheaper item and sending it without human confirmation.
- AI policy interpretation in MVP.
- Payment, marketplace, inventory, courier booking or full gifting fulfilment.
- Storing recipient home addresses.

## 4. Example workflow

```text
Salesforce / Odoo / gifting application
               |
               | gifting request (recipient company, value, category, context)
               v
         GiftGuard API
               |
               v
       Organisation lookup
               |
               v
      Active policy + rules
               |
               v
         Rule evaluation
          /     |      \
      APPROVE  BLOCK  REVIEW
         |       |       |
         v       v       v
   Allow next  Stop send  Compliance
   workflow    + reason   reviewer
          \      |       /
           \     v      /
             Audit log
               |
               v
       Response to source app
```

1. A sender chooses a gift in the customer's existing application.
2. That application sends only the minimum required data to GiftGuard.
3. GiftGuard finds the recipient organisation's active, authorised policy.
4. The rule engine evaluates amount, currency, category, deal stage and frequency.
5. It returns a decision and human-readable reason.
6. A reviewer handles exceptions if needed.
7. The source application proceeds only when its own workflow receives an approved result.
8. GiftGuard stores an audit record, not the recipient's residential address.

## 5. Odoo Standard vs OCA vs custom development

| Requirement | Odoo 18 Standard | OCA candidate | Individual Python development |
|---|---|---|---|
| Contacts / organisation records | Contacts (`res.partner`) | Not needed for basic records | Extend partner with policy reference only if justified |
| Sales / opportunity context | CRM + Sales | Depends on workflow | Optional connector to `crm.lead` / `sale.order` |
| User roles and access | Groups, ACLs, record rules | Not needed | Define GiftGuard roles and restrictive ACLs |
| Approval | Activities / Discuss / approval-related apps vary by edition and setup | `base_tier_validation` or `sale_tier_validation` may be evaluated for relevant approval flow; verify exact dependency/version | GiftGuard decision state and reviewer action |
| Inventory / delivery | Inventory / Delivery | `sale_stock_delivery_address` (OCA 18.0) supports per-line delivery addresses and split deliveries | Do not store recipient home addresses in MVP |
| Product bundles | Sales products / kits depending on setup | `sale_product_set` (OCA 18.0) for sales product sets | Not required for compliance MVP |
| Compliance policy schema | No dedicated recipient-company gift policy engine identified in standard apps | No verified OCA module identified for this exact use case | `giftguard.policy`, `giftguard.rule` |
| Decision engine | No dedicated recipient-company gifting compliance engine identified | No verified OCA module identified | Python rule evaluator |
| Decision audit trail | Chatter/logging available for general records | Generic audit modules may be evaluated | `giftguard.request` and immutable-style decision snapshots |
| External API | Odoo HTTP controllers / external API options depend on deployment | Not needed | Authenticated JSON controller |
| Recipient privacy handoff | Address book and delivery workflow are standard capabilities | Delivery-address module may help operational routing | Later: one-time recipient token / provider integration |

**OCA caution:** OCA modules are community-maintained third-party addons, not Odoo Standard. Check branch, licence, dependencies, maintenance and hosting compatibility before installing. `sale_stock_delivery_address` is an operations/delivery feature, not compliance verification.

## 6. Technology stack — Python-first recommendation for Systema Ops

| Layer | Recommended technology | Reason |
|---|---|---|
| ERP / application | Odoo 18 | Existing business platform and native users, contacts, CRM and audit workflow |
| Backend | Python (Odoo ORM, models, business methods, controllers) | Keeps business logic in Python and avoids a second backend |
| API | Odoo HTTP JSON controller | Exposes a narrow integration endpoint for external ERP/CRM tools |
| Frontend | Odoo native backend views (XML form/list/search views) | Reuses Odoo UI; no React/Vue frontend required |
| Database | PostgreSQL through Odoo ORM | Native Odoo persistence, transactions and access controls |
| Authentication | Odoo user/API credential or dedicated integration credential; rotate secrets | Avoid hard-coded shared tokens; production auth needs security review |
| Tests | Python `unittest` / Odoo `TransactionCase` | Test rules, roles, API and audit behavior |
| Deployment | Systema Ops' approved Odoo 18 environment; Docker only if the existing deployment uses it | Avoid introducing infrastructure unnecessarily |
| Observability | Odoo logs + decision audit records | Trace why a request was approved or blocked |

“Completely Python” should mean business logic, API and tests are Python. Odoo still requires XML for module metadata, access-control declarations and native views. This is standard Odoo development, not a separate JavaScript frontend. Do not add FastAPI, Streamlit or a second database to the first Odoo MVP unless a real deployment requirement demands it.

## 7. Architecture: frontend, backend and database

- **Frontend:** Odoo list/form/search views defined in XML. Users create policies, rules and requests from the Odoo interface.
- **Backend:** Python models implement policy lifecycle, rule validation, evaluation and reviewer decisions. A Python HTTP controller exposes the integration endpoint.
- **Database:** PostgreSQL stores organisations, policies, rules, requests and decision snapshots via Odoo ORM.
- **External systems:** Odoo CRM/Salesforce/Sendoso/Reachdesk can call the API only where supported and authorised. Connector development is a separate task per provider.
- **Privacy:** MVP stores business email only if required, recipient organisation, gift metadata and a pseudonymous recipient key. It does not collect home addresses.

## 8. Suggested folder structure

```text
giftguard_compliance/
├── __init__.py
├── __manifest__.py
├── controllers/
│   ├── __init__.py
│   └── api.py
├── models/
│   ├── __init__.py
│   ├── organisation.py
│   ├── policy.py
│   ├── rule.py
│   └── request.py
├── security/
│   ├── giftguard_security.xml
│   └── ir.model.access.csv
├── views/
│   ├── menu_views.xml
│   ├── organisation_views.xml
│   ├── policy_views.xml
│   └── request_views.xml
├── tests/
│   ├── __init__.py
│   └── test_rule_engine.py
└── README.md
```

## 9. Build plan

### Stage 0 — Validate before coding
1. Demo Sendoso Policy Center and SmartDelivery; capture which policies are configured by the sender's account and whether recipient-employer policy can be sourced.
2. Demo Reachdesk Address Confirmation and its policy controls.
3. Interview 5–10 corporate gifting buyers / compliance owners / sales operations staff.
4. Ask for anonymised examples of rejected gifts, approval delays and current policy-check process.
5. Confirm at least one organisation is willing to provide an approved policy and test the workflow.

**Gate:** If no customer can provide recipient-employer policy data, do not build automated cross-company policy verification as the core promise. Consider a customer-managed policy registry for the sender's own organisation instead.

### Stage 1 — Odoo MVP
1. Install addon in a disposable Odoo 18 development database.
2. Create organisations, policies and rule records.
3. Implement deterministic Python checks.
4. Add request form and reviewer action.
5. Add JSON API with integration authentication.
6. Add automated tests and sample demo data.
7. Test permissions and audit trail.

### Stage 2 — Pilot
- Run with one consenting organisation and synthetic/anonymised gift requests.
- Compare GiftGuard decisions with a compliance owner's manual decision.
- Measure false approvals, false blocks, review rate and response time.
- Do not send real gifts automatically during the pilot.

### Stage 3 — Integrations
- Add one connector selected by a pilot customer.
- Map source-system gift request fields to GiftGuard API.
- Return a decision and external request ID.
- Add retries, idempotency, rate limits and monitoring.

### Stage 4 — Privacy-preserving delivery (only if validated)
- Integrate with an existing address-confirmation/fulfilment provider.
- Use a one-time token or provider-managed address collection.
- Keep residential address hidden from sender and avoid storing it unless strictly necessary.
- Conduct privacy/security review before production.

## 10. MVP acceptance criteria

- A policy has an organisation, source, owner, effective date, review date and active status.
- Expired or unverified policies cannot silently produce an `approved` decision.
- Gift value is checked in a known currency; currency mismatch returns `review_required`.
- Prohibited category returns `blocked`.
- Amount above a hard cap returns `blocked`; amount above an approval threshold returns `review_required`.
- Deal-stage restriction returns `review_required` or `blocked` according to configured rule.
- Every evaluation records the policy version and reason.
- Only compliance reviewers can resolve review-required requests.
- Integration endpoint rejects unauthenticated calls.
- API never returns a recipient's home address.
- Tests cover normal, edge, permission and API cases.

## 11. Risks and safeguards

1. **Policy availability:** Employer policies may be confidential or not machine-readable. Require organisation-authorised policy submission and named policy owners.
2. **Legal interpretation:** The tool is workflow support, not legal advice or a guarantee of compliance. A human compliance owner approves policy configuration.
3. **Stale rules:** Enforce review dates and make expired policies require review.
4. **False approvals:** Fail closed (`review_required`) when policy is missing, expired, ambiguous or currency cannot be converted reliably.
5. **Privacy:** Minimise personal data; define retention, access, deletion and lawful basis with customer counsel.
6. **Integration scope:** Start with Odoo and one customer-selected external system. Do not promise universal plug-and-play connectors.
7. **Competitor overlap:** Sendoso already advertises address handling and policy controls. Differentiate only if interviews prove recipient-employer policy verification is missing and valuable.

## 12. Product positioning (provisional)

> GiftGuard is a Python-based, ERP-integrated gifting decision service that checks gift requests against organisation-authorised gifting policies and returns an explainable decision before dispatch.

Do not use “automatically verifies every recipient's company policy” until policy access and accuracy are proven.

## 13. Research references

- Sendoso SmartDelivery: https://support.sendoso.com/hc/en-us/articles/40631957347867-SmartDelivery
- Sendoso Policy Center updates: https://www.sendoso.com/whats-new
- Sendoso platform: https://www.sendoso.com/
- Reachdesk Address Confirmation: https://www.reachdesk.com/address-confirmation
- Odoo 18 HTTP controllers: https://www.odoo.com/documentation/18.0/developer/reference/backend/http.html
- Odoo 18 security: https://www.odoo.com/documentation/18.0/developer/reference/backend/security.html
- OCA sale-workflow (18.0 modules): https://github.com/OCA/sale-workflow
- OCA `sale_stock_delivery_address`: https://apps.odoo.com/apps/modules/18.0/sale_stock_delivery_address

**Research note:** Public vendor pages establish advertised features, not every implementation detail. Competitor demos, plan eligibility, configuration and customer interviews are still required.
