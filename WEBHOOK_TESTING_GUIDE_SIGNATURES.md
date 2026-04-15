# Webhook Testing Guide - Signature Generation Fix

**Date:** April 14, 2026  
**Status:** Updated with correct HMAC signature generation  

---

## 🔴 Previous Issue

Your earlier test failed with **401 Unauthorized** because the Authorization header was receiving the **raw WEBHOOK_SECRET** instead of the **calculated HMAC-SHA256 signature**.

```javascript
// ❌ WRONG - You did this:
Authorization: Bearer d0e229af843d1f1cc67ecb28e677c3e730f24ca33aed78dbd85d8b5b7aa453ce
// This is the raw secret, not the signature!

// ✅ CORRECT - Should be:
Authorization: Bearer <hmac_sha256_hash>
// Example: Bearer a3e8db97950496aa3ca09feeb2b4a8e626ec9f3557986d5f4f391ce7ef16a3c6
```

---

## 🔑 How Signatures Are Calculated

**Backend Formula:**
```
Payload = METHOD + URI + BODY
Signature = HMAC-SHA256(Payload, WEBHOOK_SECRET)
Authorization: Bearer <Signature>
```

**Example:**
```
Method:           POST
URI:              /api/webhooks/insurance-events
Body (compact):   {"event_type":"enrollment_created","event_id":"evt_...","agent_id":"...","agent_email":"...","enrollment_count":1,"timestamp":"..."}
Secret:           d0e229af843d1f1cc67ecb28e677c3e730f24ca33aed78dbd85d8b5b7aa453ce

Payload:          POST/api/webhooks/insurance-events{"event_type":"enrollment_created",...}
Signature:        60a22f6e1c0153bdc9bf05825f7744bdc2a681701b914a6783b976af8ebc5879
```

---

## ⚠️ CRITICAL: Backend Configuration

Before testing, **verify the WEBHOOK_SECRET is correctly set on the production server**:

### Option 1: Check Environment Variables on Cloud Run
```bash
gcloud run services describe field-tracker \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env[*].value)"
```

### Option 2: Check the .env File
The backend should have:
```env
WEBHOOK_SECRET=d0e229af843d1f1cc67ecb28e677c3e730f24ca33aed78dbd85d8b5b7aa453ce
```

### Option 3: Redeploy if Changed
If you updated `.env.example` or environment variables, **redeploy the backend** to Google Cloud Run:
```bash
gcloud run deploy field-tracker \
  --set-env-vars WEBHOOK_SECRET=d0e229af843d1f1cc67ecb28e677c3e730f24ca33aed78dbd85d8b5b7aa453ce
```

---

## ✅ Testing Methods

### Method 1: Using Updated Postman Collection (Recommended)

**What's New:**
- Pre-request script now **automatically generates** the HMAC-SHA256 signature
- The signature is calculated from: METHOD + URI + request body
- No more manual signature calculation needed

**Steps:**
1. Download the updated collection: `Lashma_Webhook_Integration.postman_collection.json`
2. Open Postman → Import
3. Set environment variables:
   - `webhook_secret`: `d0e229af843d1f1cc67ecb28e677c3e730f24ca33aed78dbd85d8b5b7aa453ce`
   - `base_url`: `https://lashma-field-tracker-1010591944835.us-central1.run.app`
   - `agent_id`: your agent UUID
   - `agent_email`: your email
4. Click "Send" on any request
5. Postman automatically generates the signature before sending

**What Postman Does Behind the Scenes:**
```javascript
// Pre-request script calculates:
const body = JSON.stringify({
  event_type: "enrollment_created",
  event_id: eventId,
  agent_id: agentId,
  agent_email: agentEmail,
  enrollment_count: 1,
  timestamp: isoTimestamp
});

const payload = "POST/api/webhooks/insurance-events" + body;
const signature = crypto.createHmac('sha256', secret).update(payload).digest('hex');
```

---

### Method 2: Using cURL Script

**Simple Test:**
```bash
./test_webhook_curl.sh
```

**What It Does:**
1. Generates unique event ID and timestamp
2. Creates compact JSON body
3. Calculates HMAC-SHA256 signature
4. Sends request with correct Authorization header
5. Shows response

**Output Example:**
```
═════════════════════════════════════════════════════════════
Webhook Test - Enrollment Created Event
═════════════════════════════════════════════════════════════

Event Details:
  Event ID:  evt_20260414084321_505672
  Timestamp: 2026-04-14T07:43:21Z
  Secret:    d0e229af843d1f1c...d85d8b5b7aa453ce

Signature Calculation:
  Method:   POST
  URI:      /api/webhooks/insurance-events
  Body:     {"event_type":"enrollment_created",...}

Calculated Signature:
  60a22f6e1c0153bdc9bf05825f7744bdc2a681701b914a6783b976af8ebc5879

...

HTTP Status: 200
Response: {"success":true,"message":"Event processed successfully","eventId":"evt_20260414084321_505672"}

✓ SUCCESS - Event processed!
```

---

### Method 3: Using Python Script

**Run the Debug Script:**
```bash
/Users/mac/connect/lashma/lashma-backend/.venv/bin/python debug_signature.py
```

**Manually Calculate Signature:**
```python
import hmac
import hashlib
import json

webhook_secret = "d0e229af843d1f1cc67ecb28e677c3e730f24ca33aed78dbd85d8b5b7aa453ce"
event_data = {
    "event_type": "enrollment_created",
    "event_id": "evt_20250814_001",
    "agent_id": "test_agent",
    "agent_email": "test@lashma.com",
    "enrollment_count": 1,
    "timestamp": "2025-08-14T14:30:00Z"
}

body = json.dumps(event_data, separators=(',', ':'))
payload = "POST/api/webhooks/insurance-events" + body
signature = hmac.new(webhook_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

print(f"Signature: {signature}")
# Use this in Authorization header: Bearer {signature}
```

---

### Method 4: Manual cURL Command

```bash
# 1. Generate signature (substitute Real values)
SECRET="d0e229af843d1f1cc67ecb28e677c3e730f24ca33aed78dbd85d8b5b7aa453ce"
BODY='{"event_type":"enrollment_created","event_id":"evt_20250814_001","agent_id":"test_agent","agent_email":"test@lashma.com","enrollment_count":1,"timestamp":"2025-08-14T14:30:00Z"}'
PAYLOAD="POST/api/webhooks/insurance-events${BODY}"
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -mac HMAC -macopt "key:${SECRET}" -hex | sed 's/^.* //')

# 2. Send request
curl -X POST 'https://lashma-field-tracker-1010591944835.us-central1.run.app/api/webhooks/insurance-events' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${SIGNATURE}" \
  -d "${BODY}"
```

---

## 🚨 Troubleshooting

### Still Getting 401 Unauthorized?

**Check These:**

1. **Is WEBHOOK_SECRET set correctly on production?**
   - Value: `d0e229af843d1f1cc67ecb28e677c3e730f24ca33aed78dbd85d8b5b7aa453ce`
   - Method: Environment variable or Cloud Run secret
   - Did you restart the backend after changing it?

2. **Is the JSON body exactly right?**
   - No spaces after colons or commas (compact JSON)
   - All field names lowercase
   - Fields in correct order (though order shouldn't matter for JSON.stringify)
   - No extra fields (like `signature:` in body)

3. **Is the URI correct?**
   - Must be: `/api/webhooks/insurance-events`
   - Request path from the server's perspective (not full URL)

4. **Is the method correct?**
   - Must be: `POST`
   - Uppercase

5. **Check Backend Logs:**
   - Cloud Run logs show HMAC debug info:
     ```
     HMAC Debug Info:
     Method: POST
     URI: /api/webhooks/insurance-events
     Body length: ... Body preview: {...}
     Received Signature: ...
     Expected Signature: ...
     Signatures match: false
     ```

---

## ✨ Key Points to Remember

| Item | Value |
|------|-------|
| **Endpoint** | `https://lashma-field-tracker-1010591944835.us-central1.run.app/api/webhooks/insurance-events` |
| **Method** | `POST` |
| **Header** | `Authorization: Bearer <HMAC-SHA256-signature>` |
| **Formula** | `HMAC-SHA256(POST + /api/webhooks/insurance-events + body, secret)` |
| **Body Format** | Compact JSON, no `signature` field |
| **Content-Type** | `application/json` |
| **Successful Response** | `200 OK` with `{"success":true,...}` |
| **Authentication Error** | `401 Unauthorized` - check signature & secret |

---

## 📊 Next Steps

1. **Verify WEBHOOK_SECRET** is deployed to production
2. **Try Postman** with the updated collection (pre-request script now auto-generates signatures)
3. **If still failing**, run `./test_webhook_curl.sh` to see exact signature being calculated
4. **Check Cloud Run logs** for HMAC debug messages
5. **Contact integration team** if issue persists

---

**Last Updated:** April 14, 2026  
**Collection Version:** 2.1 (with signature generation)
