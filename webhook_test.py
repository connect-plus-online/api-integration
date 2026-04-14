#!/usr/bin/env python3

"""
Lashma Webhook Integration Test Suite

This script tests the webhook integration between Insurance App and Field Tracker.
It generates HMAC-SHA256 signatures, sends webhook events, and validates responses.

Usage:
    python webhook_test.py
    python webhook_test.py --interactive
    python webhook_test.py --webhook-secret <secret> --base-url <url> --agent-id <id> --agent-email <email>

Requirements:
    pip install requests python-dotenv
"""

import json
import hmac
import hashlib
import uuid
import requests
import os
import sys
from datetime import datetime
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from dotenv import load_dotenv


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


@dataclass
class Config:
    webhook_secret: str
    base_url: str
    agent_id: str
    agent_email: str
    event_prefix: str = None

    def __post_init__(self):
        if not self.event_prefix:
            self.event_prefix = f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}"


class WebhookSignatureGenerator:
    """Generate HMAC-SHA256 signatures for webhook requests"""

    @staticmethod
    def generate_signature(method: str, uri: str, body: str, secret: str) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload

        Args:
            method: HTTP method (POST, GET, etc.)
            uri: Request URI path
            body: Request body as JSON string
            secret: Webhook secret key

        Returns:
            Hex-encoded HMAC-SHA256 signature
        """
        payload = method + uri + body
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature


class WebhookTester:
    """Test webhook integration with Field Tracker"""

    def __init__(self, config: Config):
        self.config = config
        self.endpoint = f"{config.base_url}/api/webhooks/insurance-events"
        self.event_counter = 0
        self.test_results = []

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        self.event_counter += 1
        return f"{self.config.event_prefix}_{self.event_counter}"

    def _generate_payment_id(self) -> str:
        """Generate unique payment ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"pay_{timestamp}_{uuid.uuid4().hex[:8]}"

    def _get_iso_timestamp(self) -> str:
        """Get current ISO 8601 timestamp"""
        return datetime.utcnow().isoformat() + 'Z'

    def _send_webhook(self, event_data: Dict) -> Tuple[int, Dict]:
        """
        Send webhook event to Field Tracker

        Args:
            event_data: Event payload dictionary

        Returns:
            Tuple of (status_code, response_json)
        """
        # Convert to JSON string
        body_json = json.dumps(event_data)

        # Generate signature
        signature = WebhookSignatureGenerator.generate_signature(
            'POST',
            '/api/webhooks/insurance-events',
            body_json,
            self.config.webhook_secret
        )

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {signature}'
        }

        try:
            response = requests.post(
                self.endpoint,
                data=body_json,
                headers=headers,
                timeout=10
            )
            return response.status_code, response.json()
        except requests.exceptions.Timeout:
            return 500, {'error': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            return 500, {'error': 'Connection refused - is Field Tracker running?'}
        except Exception as e:
            return 500, {'error': str(e)}

    def _print_result(self, test_name: str, status_code: int, expected_code: int, response: Dict):
        """Print test result with color coding"""
        passed = status_code == expected_code
        result = {
            'name': test_name,
            'passed': passed,
            'status_code': status_code,
            'expected': expected_code,
            'response': response
        }
        self.test_results.append(result)

        status_icon = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
        status_color = Colors.GREEN if passed else Colors.RED

        print(f"\n{status_icon} {Colors.BOLD}{test_name}{Colors.RESET}")
        print(f"  Status: {status_color}{status_code}{Colors.RESET} (expected {expected_code})")
        
        if response:
            if 'success' in response:
                print(f"  Response: {Colors.CYAN}{response.get('message', '')}{Colors.RESET}")
            if 'error' in response:
                print(f"  Error: {Colors.RED}{response.get('error', '')}{Colors.RESET}")
            if 'message' in response and 'error' in response:
                print(f"  Message: {Colors.YELLOW}{response.get('message', '')}{Colors.RESET}")

    def test_enrollment_created(self, count: int = 1) -> bool:
        """Test enrollment_created event"""
        event_id = self._generate_event_id()
        event_data = {
            'event_type': 'enrollment_created',
            'event_id': event_id,
            'agent_id': self.config.agent_id,
            'agent_email': self.config.agent_email,
            'enrollment_count': count,
            'timestamp': self._get_iso_timestamp(),
            'signature': 'placeholder'  # Field Tracker ignores this
        }

        status_code, response = self._send_webhook(event_data)
        self._print_result(
            f'Enrollment Created (count={count})',
            status_code,
            200,
            response
        )
        return status_code == 200

    def test_payment_processed(self, status: str = 'completed', payment_type: str = 'recurring', amount: int = 50000) -> Tuple[bool, str]:
        """
        Test payment_processed event

        Args:
            status: Payment status (completed, pending, failed, refunded)
            payment_type: Payment type (recurring, one_time)
            amount: Amount in smallest currency unit

        Returns:
            Tuple of (success, payment_id)
        """
        payment_id = self._generate_payment_id()
        event_id = self._generate_event_id()
        event_data = {
            'event_type': 'payment_processed',
            'event_id': event_id,
            'agent_id': self.config.agent_id,
            'agent_email': self.config.agent_email,
            'payment_id': payment_id,
            'payment_status': status,
            'payment_type': payment_type,
            'amount': amount,
            'currency': 'NGN',
            'timestamp': self._get_iso_timestamp(),
            'signature': 'placeholder'
        }

        status_code, response = self._send_webhook(event_data)
        self._print_result(
            f'Payment Processed ({status}, {payment_type})',
            status_code,
            200,
            response
        )
        return status_code == 200, payment_id

    def test_payment_status_update(self, payment_id: str, previous_status: str, current_status: str, failure_reason: Optional[str] = None) -> bool:
        """
        Test payment_status_updated event

        Args:
            payment_id: Payment ID from original payment_processed event
            previous_status: Original payment status
            current_status: New payment status
            failure_reason: Optional failure reason if status is 'failed'

        Returns:
            Success status
        """
        event_id = self._generate_event_id()
        event_data = {
            'event_type': 'payment_status_updated',
            'event_id': event_id,
            'agent_id': self.config.agent_id,
            'agent_email': self.config.agent_email,
            'payment_id': payment_id,
            'previous_status': previous_status,
            'current_status': current_status,
            'failure_reason': failure_reason,
            'timestamp': self._get_iso_timestamp(),
            'signature': 'placeholder'
        }

        status_code, response = self._send_webhook(event_data)
        self._print_result(
            f'Payment Status Update ({previous_status} → {current_status})',
            status_code,
            200,
            response
        )
        return status_code == 200

    def test_invalid_signature(self) -> bool:
        """Test that invalid signature is rejected (401)"""
        event_data = {
            'event_type': 'enrollment_created',
            'event_id': self._generate_event_id(),
            'agent_id': self.config.agent_id,
            'agent_email': self.config.agent_email,
            'enrollment_count': 1,
            'timestamp': self._get_iso_timestamp(),
            'signature': 'placeholder'
        }

        # Send with invalid signature
        body_json = json.dumps(event_data)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer invalid_signature_xyz'
        }

        try:
            response = requests.post(
                self.endpoint,
                data=body_json,
                headers=headers,
                timeout=10
            )
            status_code = response.status_code
            response_json = response.json() if response.text else {}
        except Exception as e:
            status_code = 500
            response_json = {'error': str(e)}

        self._print_result(
            'Invalid Signature (should be 401)',
            status_code,
            401,
            response_json
        )
        return status_code == 401

    def test_missing_fields(self) -> bool:
        """Test that missing required fields are rejected (400)"""
        # Send incomplete event
        event_data = {
            'event_type': 'enrollment_created',
            'event_id': self._generate_event_id()
            # Missing: agent_id, agent_email, enrollment_count, timestamp
        }

        body_json = json.dumps(event_data)
        signature = WebhookSignatureGenerator.generate_signature(
            'POST',
            '/api/webhooks/insurance-events',
            body_json,
            self.config.webhook_secret
        )

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {signature}'
        }

        try:
            response = requests.post(
                self.endpoint,
                data=body_json,
                headers=headers,
                timeout=10
            )
            status_code = response.status_code
            response_json = response.json() if response.text else {}
        except Exception as e:
            status_code = 500
            response_json = {'error': str(e)}

        self._print_result(
            'Missing Required Fields (should be 400)',
            status_code,
            400,
            response_json
        )
        return status_code == 400

    def test_duplicate_event(self) -> bool:
        """Test that duplicate events are handled gracefully"""
        event_id = self._generate_event_id()
        event_data = {
            'event_type': 'enrollment_created',
            'event_id': event_id,
            'agent_id': self.config.agent_id,
            'agent_email': self.config.agent_email,
            'enrollment_count': 1,
            'timestamp': self._get_iso_timestamp(),
            'signature': 'placeholder'
        }

        # Send first time - should succeed
        body_json = json.dumps(event_data)
        signature = WebhookSignatureGenerator.generate_signature(
            'POST',
            '/api/webhooks/insurance-events',
            body_json,
            self.config.webhook_secret
        )

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {signature}'
        }

        requests.post(self.endpoint, data=body_json, headers=headers, timeout=10)

        # Send duplicate - should also return 200 (idempotent)
        try:
            response = requests.post(
                self.endpoint,
                data=body_json,
                headers=headers,
                timeout=10
            )
            status_code = response.status_code
            response_json = response.json() if response.text else {}
        except Exception as e:
            status_code = 500
            response_json = {'error': str(e)}

        self._print_result(
            'Duplicate Event (should be idempotent 200)',
            status_code,
            200,
            response_json
        )
        return status_code == 200

    def print_summary(self):
        """Print test summary"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed

        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"Total Tests:  {total}")
        print(f"Passed:       {Colors.GREEN}{passed}{Colors.RESET}")
        print(f"Failed:       {Colors.RED}{failed}{Colors.RESET}")
        print(f"Success Rate: {Colors.CYAN}{(passed/total*100):.1f}%{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")

        return failed == 0


def get_config() -> Config:
    """Get configuration from environment or user input"""
    load_dotenv()

    webhook_secret = os.getenv('WEBHOOK_SECRET') or input('Enter WEBHOOK_SECRET: ')
    base_url = os.getenv('BASE_URL') or input('Enter BASE_URL (default: http://localhost:3000): ') or 'http://localhost:3000'
    agent_id = os.getenv('AGENT_ID') or input('Enter AGENT_ID (default: agent_uuid_test): ') or 'agent_uuid_test'
    agent_email = os.getenv('AGENT_EMAIL') or input('Enter AGENT_EMAIL (default: test@lashma.com): ') or 'test@lashma.com'

    return Config(
        webhook_secret=webhook_secret,
        base_url=base_url,
        agent_id=agent_id,
        agent_email=agent_email
    )


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}Lashma Webhook Integration Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    # Get configuration
    config = get_config()
    print(f"\n{Colors.CYAN}Configuration:{Colors.RESET}")
    print(f"  Base URL:     {Colors.GREEN}{config.base_url}{Colors.RESET}")
    print(f"  Agent ID:     {Colors.GREEN}{config.agent_id}{Colors.RESET}")
    print(f"  Agent Email:  {Colors.GREEN}{config.agent_email}{Colors.RESET}")
    print(f"  Secret Length: {Colors.GREEN}{len(config.webhook_secret)} chars{Colors.RESET}\n")

    tester = WebhookTester(config)

    # Test 1: Basic enrollment event
    print(f"\n{Colors.BOLD}Test Group 1: Basic Events{Colors.RESET}")
    print("-" * 60)
    tester.test_enrollment_created(count=1)

    # Test 2: Bulk enrollment
    tester.test_enrollment_created(count=5)

    # Test 3: Payment processed (successful)
    print(f"\n{Colors.BOLD}Test Group 2: Payment Events{Colors.RESET}")
    print("-" * 60)
    success, payment_id_1 = tester.test_payment_processed(status='completed', payment_type='recurring', amount=50000)

    # Test 4: Payment processed (failed)
    success, payment_id_2 = tester.test_payment_processed(status='failed', payment_type='one_time', amount=100000)

    # Test 5: Payment processed (pending)
    success, payment_id_3 = tester.test_payment_processed(status='pending', payment_type='recurring', amount=75000)

    # Test 6: Payment status update (pending → completed)
    print(f"\n{Colors.BOLD}Test Group 3: Status Updates{Colors.RESET}")
    print("-" * 60)
    tester.test_payment_status_update(payment_id_3, 'pending', 'completed')

    # Test 7: Payment status update (completed → failed - chargeback)
    tester.test_payment_status_update(payment_id_1, 'completed', 'failed', failure_reason='chargeback')

    # Test 8: Error cases
    print(f"\n{Colors.BOLD}Test Group 4: Error Handling{Colors.RESET}")
    print("-" * 60)
    tester.test_invalid_signature()
    tester.test_missing_fields()
    tester.test_duplicate_event()

    # Print summary
    success = tester.print_summary()

    if success:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ Some tests failed!{Colors.RESET}\n")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
