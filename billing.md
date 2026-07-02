# CTF Arena Billing Guide

Billing, plans, and subscription management for CTF Arena SaaS Edition.

---

## Plans

| Plan | Users | Competitions | Challenges | Containers | AI Tokens | Storage |
|---|---|---|---|---|---|---|
| **Free** | 100 | 1 | 50 | 5 | 10,000 | 512 MB |
| **Professional** | 1,000 | 10 | 500 | 50 | 500,000 | 10 GB |
| **Enterprise** | ∞ | ∞ | ∞ | ∞ | ∞ | ∞ |

Unlimited is represented as `-1` in the database and API responses.

---

## Billing States

```
trial ──────────────► active ──────────────► past_due ──────► cancelled
                         │                      │
                         └──────────────────────┘
                              (both → cancelled)
```

| State | Meaning |
|---|---|
| `trial` | 14-day evaluation period; full plan features active |
| `active` | Paid subscription in good standing |
| `past_due` | Payment failed; features may be restricted in production |
| `cancelled` | Subscription ended; terminal state |

> **Note**: Phase 15 implements the state machine only. No live payment SDK calls are made. In production, payment provider webhooks (Stripe/Razorpay) update the `status` field via `BillingService`.

---

## Allowed State Transitions

| From | To | Trigger |
|---|---|---|
| `trial` | `active` | User upgrades plan |
| `active` | `past_due` | Payment webhook failure |
| `active` | `cancelled` | User cancels |
| `past_due` | `active` | Successful payment retry |
| `past_due` | `cancelled` | User cancels while past due |
| `cancelled` | _(none)_ | Terminal state |

---

## BillingService API

```python
from app.services.billing_service import BillingService

# Get or create billing record for org
billing = BillingService.get_billing(org)

# Upgrade plan (trial → active or plan switch)
success, msg = BillingService.upgrade(org, 'professional', actor_id=user.id)

# Mark past due (simulate failed payment)
success, msg = BillingService.mark_past_due(org, actor_id=user.id)

# Cancel subscription
success, msg = BillingService.cancel(org, actor_id=user.id)

# Check if org has active billing
is_active = BillingService.is_active(org)  # True for trial or active
```

---

## Admin UI

### `/admin/organization/billing`
- Shows current plan and billing status badge
- Displays state machine diagram
- Provides plan selector cards (Free / Professional / Enterprise)

### Plan Change Flow

1. Admin visits `/admin/organization/billing`
2. Selects target plan card
3. POST to `/admin/organization/plan`
4. `BillingService.upgrade()` transitions the state machine
5. Audit log entry `plan_changed` is written
6. Flash message confirms success

---

## Future: Live Payment Integration

To wire in Stripe or Razorpay in a future phase:

1. Create a webhook endpoint (e.g. `POST /webhooks/stripe`)
2. Verify the webhook signature
3. Call the appropriate `BillingService` method based on event type:

```python
# Example Stripe webhook handler skeleton
@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    event = stripe.Webhook.construct_event(
        request.data, request.headers['Stripe-Signature'], STRIPE_SECRET
    )
    org = Organization.query.filter_by(stripe_customer_id=event['customer']).first()

    if event['type'] == 'invoice.payment_failed':
        BillingService.mark_past_due(org)
    elif event['type'] == 'invoice.paid':
        BillingService.upgrade(org, org.plan_type)
    elif event['type'] == 'customer.subscription.deleted':
        BillingService.cancel(org)
    return '', 200
```

The `OrganizationBilling` model already has `stripe_customer_id` and `razorpay_customer_id` columns for this purpose.

---

## Quota Enforcement

Quotas are enforced before every resource creation via `QuotaService.check()`:

```python
from app.services.quota_service import QuotaService

allowed, limit, used = QuotaService.check(org, 'challenges')
# allowed = True | False
# limit   = e.g. 50 (free plan)
# used    = current count (live DB query)

if not allowed:
    return error_response(f"Challenge quota reached ({used}/{limit}).", 429)
```

### Custom Quota Overrides

Admins can set per-organization custom quotas (e.g. for a special partner):

```python
org.max_users = 250    # Custom override for this org only
db.session.commit()
# org.get_quota('users') now returns 250 instead of the plan default
```

---

## Billing Data Model

```
organizations
  ├── plan_type          (current plan name)
  └── organization_billing (one-to-one)
       ├── plan_type     (billing record's plan name)
       ├── status        (trial | active | past_due | cancelled)
       ├── trial_ends_at
       ├── current_period_start
       ├── current_period_end
       ├── stripe_customer_id
       └── razorpay_customer_id
```
