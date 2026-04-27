#!/usr/bin/env python3

"""
Lashma Webhook Integration Test Suite (no HMAC — matches refactored API).

Tests enrollment_created, payment_processed, payment_status_updated against
POST {BASE_URL}/api/webhooks/insurance-events

Requirements:
    pip install requests python-dotenv

Usage:
    python webhook_test.py
    python webhook_test.py --base-url https://... --agent-email agent@lashma.com

Env (optional):
    BASE_URL, AGENT_EMAIL
"""

import json
import uuid
import requests
import os
import sys
import argparse
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv


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
    base_url: str
    agent_email: str
    event_prefix: str = None

    def __post_init__(self):
        if not self.event_prefix:
            self.event_prefix = f"evt_{datetime.now().strftime('%Y%m%d%H%M%S')}"


class WebhookTester:
    def __init__(self, config: Config):
        self.config = config
        self.endpoint = f"{config.base_url.rstrip('/')}/api/webhooks/insurance-events"
        self.event_counter = 0
        self.test_results: List[Dict] = []
        self._policy_suffix = uuid.uuid4().hex[:8]

    def _policies(self, n: int) -> List[str]:
        return [f"LSHS-TST-{self._policy_suffix}-{i + 1}" for i in range(n)]

    def _generate_event_id(self) -> str:
        self.event_counter += 1
        return f"{self.config.event_prefix}_{self.event_counter}"

    def _generate_payment_id(self) -> str:
        ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        return f"pay_{ts}_{uuid.uuid4().hex[:8]}"

    def _get_iso_timestamp(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    def _send(self, event_data: Dict) -> Tuple[int, Dict]:
        body_json = json.dumps(event_data, separators=(',', ':'))
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(
                self.endpoint,
                data=body_json.encode('utf-8'),
                headers=headers,
                timeout=30,
            )
            try:
                body = response.json() if response.text else {}
            except Exception:
                body = {'raw': response.text[:500]}
            return response.status_code, body
        except requests.exceptions.Timeout:
            return 500, {'error': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            return 500, {'error': 'Connection refused — is the API up?'}
        except Exception as e:
            return 500, {'error': str(e)}

    def _print_result(self, test_name: str, status_code: int, expected_code: int, response: Dict):
        passed = status_code == expected_code
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'status_code': status_code,
            'expected': expected_code,
            'response': response,
        })
        icon = f"{Colors.GREEN}✓{Colors.RESET}" if passed else f"{Colors.RED}✗{Colors.RESET}"
        color = Colors.GREEN if passed else Colors.RED
        print(f"\n{icon} {Colors.BOLD}{test_name}{Colors.RESET}")
        print(f"  Status: {color}{status_code}{Colors.RESET} (expected {expected_code})")
        if response:
            if 'message' in response:
                print(f"  Message: {Colors.CYAN}{response.get('message', '')}{Colors.RESET}")
            if 'error' in response:
                print(f"  Error: {Colors.RED}{response.get('error', '')}{Colors.RESET}")

    def test_enrollment_with_policies(self, enrollment_count: int, policies: List[str]) -> bool:
        event_id = self._generate_event_id()
        event_data = {
            'event_type': 'enrollment_created',
            'event_id': event_id,
            'agent_email': self.config.agent_email,
            'enrollment_count': enrollment_count,
            'policy_numbers': policies,
            'timestamp': self._get_iso_timestamp(),
        }
        code, resp = self._send(event_data)
        self._print_result(
            f'Enrollment ({enrollment_count} count, {len(policies)} policies)',
            code,
            200,
            resp,
        )
        return code == 200

    def test_payment(
        self,
        policy_numbers: List[str],
        status: str = 'completed',
        payment_type: str = 'recurring',
        amount: int = 25000,
    ) -> Tuple[bool, str]:
        payment_id = self._generate_payment_id()
        event_id = self._generate_event_id()
        event_data = {
            'event_type': 'payment_processed',
            'event_id': event_id,
            'policy_numbers': policy_numbers,
            'payment_id': payment_id,
            'payment_status': status,
            'payment_type': payment_type,
            'amount': amount,
            'currency': 'NGN',
            'timestamp': self._get_iso_timestamp(),
        }
        code, resp = self._send(event_data)
        self._print_result(
            f'Payment ({status}, {payment_type}, policies={len(policy_numbers)})',
            code,
            200,
            resp,
        )
        return code == 200, payment_id

    def test_payment_status(
        self,
        payment_id: str,
        previous_status: str,
        current_status: str,
        failure_reason: Optional[str] = None,
    ) -> bool:
        event_id = self._generate_event_id()
        event_data: Dict = {
            'event_type': 'payment_status_updated',
            'event_id': event_id,
            'payment_id': payment_id,
            'previous_status': previous_status,
            'current_status': current_status,
            'timestamp': self._get_iso_timestamp(),
        }
        if failure_reason is not None:
            event_data['failure_reason'] = failure_reason
        code, resp = self._send(event_data)
        self._print_result(
            f'Status update ({previous_status} → {current_status})',
            code,
            200,
            resp,
        )
        return code == 200

    def test_unknown_event_type(self) -> bool:
        event_data = {
            'event_type': 'not_a_real_event',
            'event_id': self._generate_event_id(),
            'timestamp': self._get_iso_timestamp(),
        }
        code, resp = self._send(event_data)
        self._print_result('Unknown event_type (expect 400)', code, 400, resp)
        return code == 400

    def test_missing_fields(self) -> bool:
        event_data = {
            'event_type': 'enrollment_created',
            'event_id': self._generate_event_id(),
        }
        code, resp = self._send(event_data)
        self._print_result('Missing required fields (expect 400)', code, 400, resp)
        return code == 400

    def test_duplicate_enrollment(self) -> bool:
        event_id = self._generate_event_id()
        event_data = {
            'event_type': 'enrollment_created',
            'event_id': event_id,
            'agent_email': self.config.agent_email,
            'enrollment_count': 1,
            'policy_numbers': [f'LSHS-DUP-{self._policy_suffix}'],
            'timestamp': self._get_iso_timestamp(),
        }
        body = json.dumps(event_data, separators=(',', ':'))
        headers = {'Content-Type': 'application/json'}
        requests.post(self.endpoint, data=body.encode('utf-8'), headers=headers, timeout=30)
        r = requests.post(self.endpoint, data=body.encode('utf-8'), headers=headers, timeout=30)
        try:
            resp = r.json() if r.text else {}
        except Exception:
            resp = {}
        self._print_result('Duplicate enrollment event_id (expect 200)', r.status_code, 200, resp)
        return r.status_code == 200

    def print_summary(self) -> bool:
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"Total Tests:  {total}")
        print(f"Passed:       {Colors.GREEN}{passed}{Colors.RESET}")
        print(f"Failed:       {Colors.RED}{failed}{Colors.RESET}")
        if total:
            print(f"Success Rate: {Colors.CYAN}{(passed/total*100):.1f}%{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
        return failed == 0


def parse_args():
    p = argparse.ArgumentParser(description='Webhook integration tests')
    p.add_argument('--base-url', default=os.getenv('BASE_URL', 'http://localhost:3000'))
    p.add_argument('--agent-email', default=os.getenv('AGENT_EMAIL', ''))
    return p.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    agent_email = args.agent_email or os.getenv('AGENT_EMAIL') or input('AGENT_EMAIL (must exist in Field Tracker): ').strip()
    if not agent_email:
        print(f"{Colors.RED}AGENT_EMAIL is required.{Colors.RESET}")
        return 1

    config = Config(base_url=args.base_url, agent_email=agent_email)
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}Lashma Webhook Test Suite (no HMAC){Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")
    print(f"{Colors.CYAN}Endpoint:{Colors.RESET} {config.base_url}/api/webhooks/insurance-events")
    print(f"{Colors.CYAN}Agent email:{Colors.RESET} {config.agent_email}\n")

    tester = WebhookTester(config)
    p1, p2 = tester._policies(2)

    print(f"\n{Colors.BOLD}Group 1: Enrollment{Colors.RESET}")
    print("-" * 60)
    tester.test_enrollment_with_policies(2, [p1, p2])
    tester.test_enrollment_with_policies(1, [f'LSHS-TST-{tester._policy_suffix}-single'])

    print(f"\n{Colors.BOLD}Group 2: Payments (uses policies from first enrollment){Colors.RESET}")
    print("-" * 60)
    ok, pay_completed = tester.test_payment([p1, p2], 'completed', 'recurring', 25000)
    ok, pay_failed = tester.test_payment([p1], 'failed', 'one_time', 100000)
    ok, pay_pending = tester.test_payment([p2], 'pending', 'recurring', 75000)

    print(f"\n{Colors.BOLD}Group 3: Status updates{Colors.RESET}")
    print("-" * 60)
    tester.test_payment_status(pay_pending, 'pending', 'completed')
    tester.test_payment_status(pay_completed, 'completed', 'failed', 'chargeback')

    print(f"\n{Colors.BOLD}Group 4: Validation & idempotency{Colors.RESET}")
    print("-" * 60)
    tester.test_unknown_event_type()
    tester.test_missing_fields()
    tester.test_duplicate_enrollment()

    ok_all = tester.print_summary()
    if ok_all:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.RESET}\n")
        return 0
    print(f"{Colors.RED}{Colors.BOLD}✗ Some tests failed.{Colors.RESET}\n")
    return 1


if __name__ == '__main__':
    sys.exit(main())
