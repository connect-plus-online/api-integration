# Lashma Webhook Integration Guide for Insurance App

**Version:** 1.0  
**Date:** April 14, 2026  
**Audience:** Insurance App Development Team  
**Purpose:** Events and API calls required to integrate with Field Tracker

---

## 1. Quick Start

### Webhook Endpoint
```
POST https://lashma-field-tracker-1010591944835.us-central1.run.app/api/webhooks/insurance-events
```

### Authentication
All requests must include HMAC-SHA256 signature in the Authorization header:
```
Authorization: Bearer <hmac_signature>
```

### Content Type
```
Content-Type: application/json
```

---

## 2. Event Types Required

Your application must send **3 event types** to the Field Tracker webhook:

| Event | Purpose | When to Send |
|-------|---------|-------------|
| `enrollment_created` | Track agent enrollments | After client enrollment completes |
| `payment_processed` | Track payment events | When payment is processed (any status) |
| `payment_status_updated` | Update payment status | When payment status changes (e.g., pending → completed) |

---

## 3. Event Details & Required Fields

### Event 1: Enrollment Created

**Trigger:** When an agent successfully enrolls a new client

```json
{
  "event_type": "enrollment_created",
  "event_id": "evt_<unique_id>",
  "agent_id": "<insurance_app_agent_uuid>",
  "agent_email": "<agent@lashma.com>",
  "enrollment_count": 1,
  "timestamp": "2025-08-11T14:30:00Z",
  "signature": "<hmac_sha256_signature>"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | ✅ | Must be exactly: `enrollment_created` |
| `event_id` | string | ✅ | Unique ID for this event (e.g., `evt_abc123xyz`) - **MUST be unique per event** |
| `agent_id` | string | ✅ | Agent's unique ID in your system |
| `agent_email` | string | ✅ | Agent's email address (field tracker uses this to map agents) |
| `enrollment_count` | integer | ✅ | Number of enrollments in this event (minimum: 1) |
| `timestamp` | string | ✅ | ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ` |
| `signature` | string | ✅ | See Section 5 for signature calculation |

**Example:**
```json
{
  "event_type": "enrollment_created",
  "event_id": "evt_20250811143000_agent001_1",
  "agent_id": "agent_uuid_5f4a8c9d",
  "agent_email": "john.doe@lashma.com",
  "enrollment_count": 3,
  "timestamp": "2025-08-11T14:30:00Z",
  "signature": "a1b2c3d4e5f6..."
}
```

---

### Event 2: Payment Processed

**Trigger:** When a payment is processed (immediately after payment transaction)

```json
{
  "event_type": "payment_processed",
  "event_id": "evt_<unique_id>",
  "agent_id": "<insurance_app_agent_uuid>",
  "agent_email": "<agent@lashma.com>",
  "payment_id": "pay_<unique_id>",
  "payment_status": "completed",
  "payment_type": "recurring",
  "amount": 25000,
  "currency": "NGN",
  "timestamp": "2025-08-11T14:35:00Z",
  "signature": "<hmac_sha256_signature>"
}
```

| Field | Type | Required | Values | Description |
|-------|------|----------|--------|-------------|
| `event_type` | string | ✅ | `payment_processed` | Event type |
| `event_id` | string | ✅ | - | Unique event ID |
| `agent_id` | string | ✅ | - | Agent's unique ID |
| `agent_email` | string | ✅ | - | Agent's email |
| `payment_id` | string | ✅ | - | Unique payment ID (e.g., `pay_ABC123XYZ`) |
| `payment_status` | string | ✅ | `pending`, `completed`, `failed`, `refunded` | Payment result |
| `payment_type` | string | ✅ | `one_time`, `recurring` | Type of payment |
| `amount` | integer | ✅ | - | Amount in smallest currency unit (for NGN: in kobo) |
| `currency` | string | ✅ | `NGN` (default) | Currency code |
| `timestamp` | string | ✅ | - | ISO 8601 timestamp |
| `signature` | string | ✅ | - | HMAC signature |

**Status Values:**
- `pending` - Payment initiated, awaiting processing
- `completed` - Payment successful
- `failed` - Payment declined/failed
- `refunded` - Payment refunded

**Example:**
```json
{
  "event_type": "payment_processed",
  "event_id": "evt_20250811143500_pay001_1",
  "agent_id": "agent_uuid_5f4a8c9d",
  "agent_email": "john.doe@lashma.com",
  "payment_id": "pay_TXN20250811_001",
  "payment_status": "completed",
  "payment_type": "recurring",
  "amount": 25000,
  "currency": "NGN",
  "timestamp": "2025-08-11T14:35:00Z",
  "signature": "b2c3d4e5f6a7..."
}
```

---

### Event 3: Payment Status Updated

**Trigger:** When payment status changes after initial processing (e.g., pending → completed, completed → failed)

```json
{
  "event_type": "payment_status_updated",
  "event_id": "evt_<unique_id>",
  "agent_id": "<insurance_app_agent_uuid>",
  "agent_email": "<agent@lashma.com>",
  "payment_id": "pay_<same_id_as_original>",
  "previous_status": "pending",
  "current_status": "completed",
  "failure_reason": null,
  "timestamp": "2025-08-11T14:40:00Z",
  "signature": "<hmac_sha256_signature>"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | ✅ | Must be exactly: `payment_status_updated` |
| `event_id` | string | ✅ | New unique ID for this status update event |
| `agent_id` | string | ✅ | Agent's unique ID |
| `agent_email` | string | ✅ | Agent's email |
| `payment_id` | string | ✅ | **Same payment_id** as original `payment_processed` event |
| `previous_status` | string | ✅ | Original status (pending, completed, failed, or refunded) |
| `current_status` | string | ✅ | New status (pending, completed, failed, or refunded) |
| `failure_reason` | string | ❌ | Optional reason if status is "failed" (e.g., "insufficient_funds") |
| `timestamp` | string | ✅ | ISO 8601 timestamp of status change |
| `signature` | string | ✅ | HMAC signature |

**Example:**
```json
{
  "event_type": "payment_status_updated",
  "event_id": "evt_20250811144000_update001_1",
  "agent_id": "agent_uuid_5f4a8c9d",
  "agent_email": "john.doe@lashma.com",
  "payment_id": "pay_TXN20250811_001",
  "previous_status": "pending",
  "current_status": "completed",
  "failure_reason": null,
  "timestamp": "2025-08-11T14:40:00Z",
  "signature": "c3d4e5f6a7b8..."
}
```

---

## 4. Data Rules & Constraints

### Field Validation Rules

**Event ID:**
- Must be unique across all events (no duplicates)
- Format: anything (recommend: `evt_<timestamp>_<identifier>_<sequence>`)
- Used for idempotency - same event_id = duplicate (will be silently ignored)

**Agent ID:**
- Your internal agent identifier (UUID recommended)
- Must be consistent across all events for the same agent
- Field Tracker uses email to look up agents initially, then creates mapping to your agent_id

**Agent Email:**
- Must be a valid email address
- Field Tracker uses this to find the agent in their system
- If agent doesn't exist in Field Tracker yet, they'll be created on first webhook

**Enrollment Count:**
- Minimum: 1
- Integer value only
- Represents number of clients enrolled in this event

**Payment ID:**
- Recommended format: `pay_<timestamp>_<unique_id>`
- Must be consistent across `payment_processed` and `payment_status_updated` for the same payment
- Different from event_id - one payment may create multiple events

**Amount:**
- Must be positive integer
- In smallest currency unit (for NGN, divide by 100 for display)
- Example: ₦250.00 = 25000 in the API

**Timestamp:**
- ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`
- Use UTC timezone (Z suffix)
- Example: `2025-08-11T14:35:00Z`

### Data Privacy

⚠️ **DO NOT SEND:**
- Client/customer personal information (names, phone numbers, personal email)
- Physical addresses or location coordinates
- Payment instrument details (card numbers, bank account numbers)
- Policy numbers linked to clients
- Beneficiary information
- Medical or health data

✅ **ONLY SEND:**
- Agent identifiers (email and ID)
- Enrollment and payment counts
- Payment transaction IDs (not card details)
- Payment status
- Timestamps

---

## 5. HMAC Signature Generation

### How to Generate the Signature

The signature is calculated using **HMAC-SHA256** algorithm:

```
Payload = HTTP_METHOD + URI_PATH + REQUEST_BODY
Signature = HMAC-SHA256(Payload, WEBHOOK_SECRET)
```

### Step-by-Step Example

**1. Your Request Details:**
```
Method: POST
URI: /api/webhooks/insurance-events
Body: {"event_type":"enrollment_created","event_id":"evt_abc123",...}
Secret: your_webhook_secret_key
```

**2. Concatenate Components:**
```
Payload = "POST" + "/api/webhooks/insurance-events" + "{\"event_type\":\"enrollment_created\",\"event_id\":\"evt_abc123\",...}"
```

**3. Generate HMAC-SHA256:**
```
Signature = HMAC-SHA256(Payload, "your_webhook_secret_key")
// Result: hex string like "a1b2c3d4e5f6..."
```

**4. Include in Request Header:**
```
Authorization: Bearer a1b2c3d4e5f6...
```

### Implementation Examples

**Node.js / JavaScript:**
```javascript
const crypto = require('crypto');

function generateSignature(method, uri, body, secret) {
  const payload = method + uri + body;
  return crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
}

// Usage
const signature = generateSignature(
  'POST',
  '/api/webhooks/insurance-events',
  JSON.stringify(eventBody),
  process.env.WEBHOOK_SECRET
);
```

**Python:**
```python
import hmac
import hashlib

def generate_signature(method, uri, body, secret):
    payload = method + uri + body
    return hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

# Usage
signature = generate_signature(
    'POST',
    '/api/webhooks/insurance-events',
    json.dumps(event_body),
    os.getenv('WEBHOOK_SECRET')
)
```

**PHP:**
```php
function generateSignature($method, $uri, $body, $secret) {
    $payload = $method . $uri . $body;
    return hash_hmac('sha256', $payload, $secret);
}

// Usage
$signature = generateSignature(
    'POST',
    '/api/webhooks/insurance-events',
    json_encode($eventBody),
    getenv('WEBHOOK_SECRET')
);
```

⚠️ **Important:** The body must be the exact JSON string (no formatting changes, preserved whitespace)

---

## 6. HTTP Response Codes

### Success Responses

**200 OK - Event Processed Successfully**
```json
{
  "success": true,
  "message": "Event processed successfully",
  "eventId": "evt_abc123xyz"
}
```
- Event was received and processed
- No action needed

---

### Error Responses

**400 Bad Request - Invalid Payload or Agent Not Found**
```json
{
  "message": "Agent not found in field tracker system",
  "error": "Bad Request",
  "statusCode": 400
}
```
**Possible causes:**
- Missing required field
- Invalid field format
- Agent email not found in Field Tracker

**Action:** Verify all required fields and that agent exists in Field Tracker system

---

**401 Unauthorized - Invalid HMAC Signature**
```json
{
  "message": "Invalid webhook signature",
  "error": "Unauthorized",
  "statusCode": 401
}
```
**Causes:**
- WEBHOOK_SECRET doesn't match
- Request body was modified in transit
- Signature calculation error

**Action:** Verify WEBHOOK_SECRET matches and signature calculation

---

**500 Internal Server Error**
```json
{
  "message": "Failed to process webhook event",
  "error": "Internal Server Error",
  "statusCode": 500
}
```
**Causes:**
- Database connection issue
- Server error

**Action:** Retry after 5 seconds (temporary failure)

---

## 7. Request/Response Examples

### Complete Enrollment Event Example

**Request:**
```bash
curl -X POST https://lashma-field-tracker-1010591944835.us-central1.run.app/api/webhooks/insurance-events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer a1b2c3d4e5f6a7b8c9d0e1f2g3h4i5j6" \
  -d '{
    "event_type": "enrollment_created",
    "event_id": "evt_20250814_agent001_enrollment_1",
    "agent_id": "agent_uuid_5f4a8c9d",
    "agent_email": "john.doe@lashma.com",
    "enrollment_count": 2,
    "timestamp": "2025-08-14T14:30:00Z",
    "signature": "a1b2c3d4e5f6a7b8c9d0e1f2g3h4i5j6"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Event processed successfully",
  "eventId": "evt_20250814_agent001_enrollment_1"
}
```

---

### Complete Payment Event Example

**Request:**
```bash
curl -X POST https://lashma-field-tracker-1010591944835.us-central1.run.app/api/webhooks/insurance-events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer b2c3d4e5f6a7b8c9d0e1f2g3h4i5j6k7" \
  -d '{
    "event_type": "payment_processed",
    "event_id": "evt_20250814_agent001_payment_1",
    "agent_id": "agent_uuid_5f4a8c9d",
    "agent_email": "john.doe@lashma.com",
    "payment_id": "pay_20250814_TXN_001",
    "payment_status": "completed",
    "payment_type": "recurring",
    "amount": 50000,
    "currency": "NGN",
    "timestamp": "2025-08-14T14:35:00Z",
    "signature": "b2c3d4e5f6a7b8c9d0e1f2g3h4i5j6k7"
  }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Event processed successfully",
  "eventId": "evt_20250814_agent001_payment_1"
}
```

---

## 8. Integration Checklist

- [ ] Implement signature generation using HMAC-SHA256
- [ ] Store WEBHOOK_SECRET securely (environment variable)
- [ ] Send enrollment_created event after client enrollment completes
- [ ] Send payment_processed event immediately after payment transaction
- [ ] Send payment_status_updated event when payment status changes
- [ ] Use consistent agent_id across all events for same agent
- [ ] Ensure event_id is unique for every event
- [ ] Use ISO 8601 timestamps (UTC timezone)
- [ ] Validate response codes and handle errors appropriately
- [ ] Test with Postman collection (provided separately)
- [ ] Log all webhook calls for debugging
- [ ] Monitor 401 errors (signature issues)
- [ ] Monitor 400 errors (missing/invalid fields)

---

## 9. Testing

### Testing Endpoint
For development/staging:
```
POST https://lashma-field-tracker-1010591944835.us-central1.run.app/api/webhooks/insurance-events
```

### Using Postman
See attached `Lashma_Webhook_Integration.postman_collection.json`

The collection includes:
- Pre-configured requests for each event type
- Pre-scripts to auto-generate event IDs, timestamps, and signatures
- Environment variables for WEBHOOK_SECRET
- Example payloads

---

## 10. Support

For questions or issues:
- Contact: Integration Team
- Email: integration@lashma.com
- Available: Monday-Friday, 9 AM - 5 PM WAT

---

## Appendix: Field Mapping Reference

### Your System → Field Tracker System

| Your Field | Field Tracker Field | Example |
|-----------|-------------------|---------|
| Agent UUID | `agent_id` | `agent_uuid_5f4a8c9d` |
| Agent Email | `agent_email` | `john.doe@lashma.com` |
| Event ID | `event_id` | `evt_20250814_123` |
| Payment ID | `payment_id` | `pay_20250814_001` |
| Enrollment Count | `enrollment_count` | `1`, `2`, `5` |
| Payment Amount (in kobo) | `amount` | `25000` (= ₦250) |

---

**Document Version:** 1.0  
**Last Updated:** April 14, 2026  
**Status:** Ready for Integration  
