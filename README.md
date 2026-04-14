# 📦 Webhook Integration Package - Quick Start

**Date:** April 14, 2026  
**For:** Lashma Insurance App Development Team  
**Status:** Ready to Integrate

---

## 📋 What You Need to Know

Your Insurance App needs to send **3 types of events** to Field Tracker whenever:
1. **An agent enrolls a new client** → Send `enrollment_created`
2. **A payment is processed** → Send `payment_processed`
3. **A payment status changes** → Send `payment_status_updated`

**That's it.** Everything else is handled by Field Tracker.

---

## 📦 Files Provided

| File | Purpose |
|------|---------|
| **WEBHOOK_INTEGRATION_GUIDE_FOR_INSURANCE_APP.md** | 📖 Complete technical guide with all event specifications |
| **Lashma_Webhook_Integration.postman_collection.json** | 🧪 Ready-to-use Postman collection for testing |
| **webhook-signature-generator.js** | 🔐 Script to generate HMAC signatures |
| **WEBHOOK_IMPLEMENTATION.md** | 📚 Implementation details (for reference) |

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Get Your Webhook Secret
Contact the integration team for your `WEBHOOK_SECRET` value (256-bit hex string).

```bash
# Example secret (DO NOT USE - get your own)
WEBHOOK_SECRET=a1b2c3d4e5f6a7b8c9d0e1f2g3h4i5j6k7l8m9n0o1p2q3r4s5t6u7v8w9x0y1z
```

### Step 2: Test with Postman (Easiest Way)

1. **Open Postman**
2. **Import collection:** `Lashma_Webhook_Integration.postman_collection.json`
3. **Set environment variables:**
   - `webhook_secret` = Your secret from Step 1
   - `base_url` = `https://field-tracker.lashma.com`
   - `agent_id` = Your internal agent UUID
   - `agent_email` = Agent's email
4. **Send test requests** (pre-scripts calculate signatures automatically)

✅ If you get `200 OK` response → You're ready!

### Step 3: Implement in Your Code

Use the examples in `WEBHOOK_INTEGRATION_GUIDE_FOR_INSURANCE_APP.md` Section 5 for your language:
- Node.js / JavaScript
- Python
- PHP
- Or any language with HMAC-SHA256 support

### Step 4: Send Real Events

Once tested, send actual webhook events:
- When enrollment completes
- When payment is processed
- When payment status changes

---

## 📡 Endpoint

```
POST https://field-tracker.lashma.com/api/webhooks/insurance-events
Authorization: Bearer <hmac_signature>
Content-Type: application/json
```

---

## 📝 The 3 Events You Send

### 1️⃣ Enrollment Created
```json
{
  "event_type": "enrollment_created",
  "event_id": "evt_unique_id",
  "agent_id": "your_agent_uuid",
  "agent_email": "agent@lashma.com",
  "enrollment_count": 1,
  "timestamp": "2025-08-14T14:30:00Z",
  "signature": "hmac_sha256_signature"
}
```
**When:** After client successfully enrolls  
**What we track:** Enrollment count per agent

---

### 2️⃣ Payment Processed
```json
{
  "event_type": "payment_processed",
  "event_id": "evt_unique_id",
  "agent_id": "your_agent_uuid",
  "agent_email": "agent@lashma.com",
  "payment_id": "pay_unique_id",
  "payment_status": "completed",
  "payment_type": "recurring",
  "amount": 25000,
  "currency": "NGN",
  "timestamp": "2025-08-14T14:35:00Z",
  "signature": "hmac_sha256_signature"
}
```
**When:** Immediately after payment transaction  
**Status values:** `pending`, `completed`, `failed`, `refunded`  
**What we track:** Payment volume, success rate, revenue per agent

---

### 3️⃣ Payment Status Updated
```json
{
  "event_type": "payment_status_updated",
  "event_id": "evt_unique_id",
  "agent_id": "your_agent_uuid",
  "agent_email": "agent@lashma.com",
  "payment_id": "pay_same_id_as_before",
  "previous_status": "pending",
  "current_status": "completed",
  "failure_reason": null,
  "timestamp": "2025-08-14T14:40:00Z",
  "signature": "hmac_sha256_signature"
}
```
**When:** When payment status changes (e.g., pending → completed)  
**Same payment_id:** Must match the original `payment_processed` event  
**What we track:** Payment outcome corrections, chargeback handling

---

## 🔐 How Signatures Work

**Don't overthink it** — just concatenate and hash:

```
Payload = METHOD + PATH + BODY
         = "POST" + "/api/webhooks/insurance-events" + "{json_body}"

Signature = HMAC-SHA256(Payload, WEBHOOK_SECRET)
```

### Using the Signature Generator
```bash
# Interactive mode (easy)
node webhook-signature-generator.js --interactive

# Command line mode
node webhook-signature-generator.js \
  --method POST \
  --uri "/api/webhooks/insurance-events" \
  --body '{"event_type":"enrollment_created",...}' \
  --secret "your_webhook_secret"
```

### Postman Does This Automatically
In Postman, pre-scripts generate signatures, so you don't need the Node script there.

---

## ✅ Success Indicators

### When Everything Works ✅
- **Response:** `HTTP 200 OK`
- **Body:** `{ "success": true, "message": "Event processed successfully", "eventId": "..." }`
- **Check Field Tracker:** Agent metrics should update in real-time

### If You Get 401 Unauthorized ❌
- **Problem:** Invalid signature
- **Solution:** 
  - Verify `WEBHOOK_SECRET` matches what the team gave you
  - Check that request body JSON is exact (no extra spaces)
  - Ensure you're using HMAC-SHA256, not HMAC-MD5 or HMAC-SHA1

### If You Get 400 Bad Request ❌
- **Problem:** Missing or invalid fields
- **Solution:**
  - Check all required fields are present
  - Verify email format, timestamps are ISO 8601, amounts are positive integers
  - See error message for specific field that's invalid

---

## 📋 Implementation Checklist

Before going to production:

- [ ] Generate webhook secret with team
- [ ] Test enrollment event with Postman
- [ ] Test payment event (completed) with Postman
- [ ] Test payment status update with Postman
- [ ] Implement signature generation in your code
- [ ] Create enrollment webhook call when client enrolls
- [ ] Create payment webhook call when payment processes
- [ ] Create status update webhook call when status changes
- [ ] Add error logging for webhook failures
- [ ] Test with real agent data (staging first)
- [ ] Monitor logs for any signature/validation errors
- [ ] Notify team when ready for production
- [ ] Set up alerts for failed webhooks (optional but recommended)

---

## 🛠️ Common Use Cases

### Use Case 1: Batch Enrollment
If agent enrolls 5 clients at once:
```json
{
  ...
  "enrollment_count": 5,
  ...
}
```
Field Tracker automatically adds 5 to the agent's total.

### Use Case 2: Recurring Monthly Payment
```json
{
  ...
  "payment_type": "recurring",
  "amount": 50000,
  ...
}
```

### Use Case 3: Payment Failed Then Succeeded
Send two events:
1. First: `payment_processed` with `payment_status: "failed"`
2. Later: `payment_status_updated` with `previous_status: "failed"`, `current_status: "completed"`

Field Tracker updates the metrics correctly.

### Use Case 4: Chargeback After Success
1. Original: `payment_processed` with `payment_status: "completed"`
2. Later: `payment_status_updated` with `previous_status: "completed"`, `current_status: "failed"`, `failure_reason: "chargeback"`

The agent's successful count decreases by 1.

---

## 🔗 Event ID Strategy

Make event IDs unique and identifiable:
```
Format: evt_[TIMESTAMP]_[TYPE]_[SEQUENCE]

Examples:
- evt_20250814143000_enrollment_1
- evt_20250814143500_payment_1
- evt_20250814144000_update_1

Why:
- Duplicate detection: Same event_id = ignored
- Debugging: Easy to trace in logs
- Unique: Prevents accidental replays
```

---

## 💡 Pro Tips

### 1. Store Payment IDs
Keep the `payment_id` handy for later status updates:
```javascript
// When payment is created:
const paymentId = "pay_" + generateUniqueId();
storePaymentId(paymentId);  // Save for later

// When status changes:
sendStatusUpdate({
  payment_id: getStoredPaymentId(),  // Use the saved ID
  previous_status: "pending",
  current_status: "completed"
});
```

### 2. Use Timestamps Wisely
```javascript
// Use current time for event_timestamp
// Field Tracker uses this to order events correctly
const timestamp = new Date().toISOString();  // ✅ Correct

// NOT:
const timestamp = "2025-01-01T00:00:00Z";  // ❌ Wrong - too old
```

### 3. Error Handling
```javascript
try {
  response = sendWebhook(event);
  if (response.status === 200) {
    logSuccess(event);
  } else if (response.status === 401) {
    logError("Check webhook secret");
  } else if (response.status === 400) {
    logError("Check required fields: " + response.body);
  }
} catch (error) {
  // Network error - retry after 5 seconds
  retryAfterDelay(error);
}
```

### 4. Don't Send PII
❌ **Don't send:**
- Customer names, phone numbers, email
- Addresses or GPS coordinates
- Card numbers or bank details
- Policy numbers
- Medical information

---

## 📞 Support

**Questions about:**
- Event specifications → See `WEBHOOK_INTEGRATION_GUIDE_FOR_INSURANCE_APP.md`
- How signatures work → See `webhook-signature-generator.js`
- Postman collection → See collection UI in Postman
- Backend implementation → See `WEBHOOK_IMPLEMENTATION.md`

**Contact:** Integration Team  
**Email:** integration@lashma.com  
**Available:** Mon-Fri, 9 AM - 5 PM WAT

---

## 📚 Document Roadmap

1. **Start here** ← You are here
2. Read `WEBHOOK_INTEGRATION_GUIDE_FOR_INSURANCE_APP.md` for full specs
3. Test with `Lashma_Webhook_Integration.postman_collection.json`
4. Use `webhook-signature-generator.js` if not using Postman
5. Reference `WEBHOOK_IMPLEMENTATION.md` for backend details (optional)

---

## 🎯 Your Next Steps

**Right now:**
1. Get your WEBHOOK_SECRET from the team
2. Export the Postman collection
3. Set environment variables in Postman
4. Send one test enrollment event

**This week:**
1. Update your code with signature generation
2. Create webhook calls in your enrollment flow
3. Create webhook calls in your payment flow
4. Test with staging data

**Next week:**
1. Review logs with the team
2. Fix any issues
3. Go live

---

**You've got this! 🚀**

For questions, reach out to the integration team.

---

*Last Updated: April 14, 2026*  
*Next Review: 30 days*
