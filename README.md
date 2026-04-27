# Webhook Integration (Insurance App)

## Endpoint
`POST /api/webhooks/insurance-events`

Production base URL:
`https://lashma-field-tracker-1010591944835.us-central1.run.app`

Header:
`Content-Type: application/json`

## Authentication
No HMAC signature required.

## Event Types
Send only these 3 event types:
- `enrollment_created`
- `payment_processed`
- `payment_status_updated`

## Payloads

### 1) enrollment_created
```json
{
  "event_type": "enrollment_created",
  "event_id": "evt_unique_id",
  "agent_email": "agent@lashma.com",
  "enrollment_count": 2,
  "policy_numbers": ["LSHS-00000001", "LSHS-00000002"],
  "timestamp": "2026-04-15T14:30:00Z"
}
```

Notes:
- `agent_email` must exist as a user in Field Tracker.
- `policy_numbers` are used to map policies to that agent.
- Preferred: `len(policy_numbers) == enrollment_count` (documented convention; not hard validation).

### 2) payment_processed
```json
{
  "event_type": "payment_processed",
  "event_id": "evt_unique_id",
  "policy_numbers": ["LSHS-00000001", "LSHS-00000002"],
  "payment_id": "pay_unique_id",
  "payment_status": "completed",
  "payment_type": "recurring",
  "amount": 25000,
  "currency": "NGN",
  "timestamp": "2026-04-15T14:35:00Z"
}
```

Notes:
- `payment_id` is globally unique.
- Payment is attributed per policy using stored policy-to-agent mapping.
- If a policy cannot be mapped, request still succeeds; unmapped policy is skipped.

### 3) payment_status_updated
```json
{
  "event_type": "payment_status_updated",
  "event_id": "evt_unique_id",
  "payment_id": "pay_same_id_as_original",
  "previous_status": "pending",
  "current_status": "completed",
  "failure_reason": null,
  "timestamp": "2026-04-15T14:40:00Z"
}
```

## Allowed Values
- `payment_status`: `pending`, `completed`, `failed`, `refunded`
- `payment_type`: `one_time`, `recurring`

## Responses
- `200`: accepted/processed
- `400`: invalid payload or `agent_email` not found

## Quick Test

### Postman
Import:
`Lashma_Webhook_Integration.postman_collection.json`

Set variables:
- `base_url`
- `agent_email`

### Python
Run:
```bash
BASE_URL=http://localhost:4040 AGENT_EMAIL=<valid_email> .venv/bin/python webhook_test.py
```

## Minimal Checklist
- Use unique `event_id` for every webhook request.
- Ensure `agent_email` exists in Field Tracker.
- Send enrollment before payment for new policy numbers.
- Use valid ISO-8601 UTC `timestamp`.
