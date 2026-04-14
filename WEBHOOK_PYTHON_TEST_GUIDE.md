# Python Webhook Test Script - Setup & Usage

## Installation

### 1. Install Python Dependencies

```bash
pip install requests python-dotenv
```

### 2. (Optional) Create .env File

Create a `.env` file in the project root with your configuration:

```env
WEBHOOK_SECRET=your_webhook_secret_key_here
BASE_URL=http://localhost:3000
AGENT_ID=agent_uuid_test
AGENT_EMAIL=test@lashma.com
```

## Usage

### Interactive Mode (Easiest)

The script prompts for configuration if not provided:

```bash
python webhook_test.py
```

Then enter your values when prompted:
- WEBHOOK_SECRET
- BASE_URL (default: http://localhost:3000)
- AGENT_ID (default: agent_uuid_test)
- AGENT_EMAIL (default: test@lashma.com)

### Using Environment Variables

```bash
export WEBHOOK_SECRET="your_secret_key"
export BASE_URL="http://localhost:3000"
export AGENT_ID="agent_uuid_123"
export AGENT_EMAIL="test@lashma.com"

python webhook_test.py
```

### Using .env File

1. Create `.env` file with your variables
2. Run the script:
```bash
python webhook_test.py
```

## What Gets Tested

### Test Group 1: Basic Events
- ✅ Single enrollment event
- ✅ Bulk enrollment (5 enrollments in one event)

### Test Group 2: Payment Events
- ✅ Payment completed (recurring payment)
- ✅ Payment failed (one-time payment)
- ✅ Payment pending (recurring payment)

### Test Group 3: Status Updates
- ✅ Payment status: pending → completed
- ✅ Payment status: completed → failed (chargeback)

### Test Group 4: Error Handling
- ✅ Invalid signature (should return 401)
- ✅ Missing required fields (should return 400)
- ✅ Duplicate event handling (idempotency)

## Expected Output

```
════════════════════════════════════════════════════════════
Lashma Webhook Integration Test Suite
════════════════════════════════════════════════════════════

Configuration:
  Base URL:      http://localhost:3000
  Agent ID:      agent_uuid_test
  Agent Email:   test@lashma.com
  Secret Length: 64 chars

Test Group 1: Basic Events
────────────────────────────────────────────────────────────
✓ Enrollment Created (count=1)
  Status: 200 (expected 200)
  Response: Event processed successfully

✓ Enrollment Created (count=5)
  Status: 200 (expected 200)
  Response: Event processed successfully

[... more tests ...]

════════════════════════════════════════════════════════════
TEST SUMMARY
════════════════════════════════════════════════════════════
Total Tests:  11
Passed:       11
Failed:       0
Success Rate: 100.0%
════════════════════════════════════════════════════════════

✓ All tests passed!
```

## Troubleshooting

### "Connection refused - is Field Tracker running?"
- Make sure the backend is running: `npm start`
- Check BASE_URL is correct
- Check port matches (default 3000)

### "Invalid webhook signature"
- Verify WEBHOOK_SECRET matches what the team gave you
- Check that the secret is correct in .env or environment variables

### "Agent not found in field tracker system"
- Make sure the agent exists in the system with the provided email
- Or the agent will be created on first webhook (if mapping exists)

### Tests take a long time
- Field Tracker might be slow
- Check server logs for errors
- Verify database connection

### Permission denied when running script
Make it executable:
```bash
chmod +x webhook_test.py
python webhook_test.py
```

## Example Workflow

### Step 1: Start Backend
```bash
# In one terminal
npm start
```

### Step 2: Set Up Environment
```bash
# Create .env file
cat > .env << EOF
WEBHOOK_SECRET=your_secret_here
BASE_URL=http://localhost:3000
AGENT_ID=agent_uuid_test
AGENT_EMAIL=test@lashma.com
EOF
```

### Step 3: Run Tests
```bash
python webhook_test.py
```

### Step 4: Check Results
- Look for "✓" marks (passed tests)
- Look for "✗" marks (failed tests)
- Check TEST SUMMARY for overall result

## Advanced Usage

### Run Specific Tests
Edit the `main()` function in `webhook_test.py` to select which tests to run:

```python
def main():
    # ... setup ...
    
    # Run only enrollment tests
    tester.test_enrollment_created(count=1)
    tester.test_enrollment_created(count=5)
    
    # Skip other tests
    # tester.test_payment_processed(...)
    # tester.test_payment_status_update(...)
```

### Modify Test Parameters
Change payment amounts, statuses, etc:

```python
# In main()
success, payment_id = tester.test_payment_processed(
    status='completed',
    payment_type='recurring',
    amount=500000  # Change amount here
)
```

### Add Custom Tests
```python
def test_custom_scenario(tester):
    """Add your own test scenario"""
    success, payment_id = tester.test_payment_processed(
        status='completed',
        payment_type='one_time',
        amount=123456
    )
    # ... more logic ...

# In main()
test_custom_scenario(tester)
```

## Debug Output

The script logs:
- Generated event IDs
- HTTP status codes
- Response messages
- Any errors

Check the output for details on what each request did.

## Integration with CI/CD

Use the exit code in CI/CD pipelines:

```bash
python webhook_test.py
if [ $? -eq 0 ]; then
    echo "All webhook tests passed!"
else
    echo "Webhook tests failed!"
    exit 1
fi
```

## Performance

- Each test takes ~1 second
- Full test suite runs in ~15 seconds
- If much slower, check Field Tracker performance

## For More Information

- See `WEBHOOK_INTEGRATION_GUIDE_FOR_INSURANCE_APP.md` for API details
- See `WEBHOOK_QUICK_START.md` for overview
- See `WEBHOOK_IMPLEMENTATION.md` for backend details
