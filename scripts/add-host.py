#!/usr/bin/env python3
"""
Script to register a new host for monitoring.

Usage:
    python add-host.py --name "Web Server 01" --host-id web01 --frequency 300

This will:
1. Generate a secure token
2. Register the host with the monitoring API
3. Display the heartbeat command to run on the client
"""
import argparse
import json
import secrets
import sys

import requests


def generate_token():
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def register_host(
    server_url: str,
    name: str,
    host_id: str,
    frequency: int,
    token: str = None,
    schedule_type: str = "always",
    grace_period: int = 60,
):
    """
    Register a new host with the monitoring system.

    Args:
        server_url: Monitoring server URL
        name: Human-readable host name
        host_id: Unique host identifier
        frequency: Expected heartbeat frequency in seconds
        token: Authentication token (generates if not provided)
        schedule_type: Monitoring schedule ('always', 'business_hours')
        grace_period: Grace period in seconds

    Returns:
        Response dictionary
    """
    if not token:
        token = generate_token()

    data = {
        "name": name,
        "host_id": host_id,
        "token": token,
        "expected_frequency_seconds": frequency,
        "schedule_type": schedule_type,
        "grace_period_seconds": grace_period,
    }

    try:
        response = requests.post(
            f"{server_url}/api/v1/hosts",
            json=data,
            timeout=10,
        )
        response.raise_for_status()
        return response.json(), token
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to register host: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            print(f"Server response: {e.response.text}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Register a new host for monitoring"
    )
    parser.add_argument(
        "--server",
        default="http://localhost:8080",
        help="Monitoring server URL (default: http://localhost:8080)",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Human-readable host name (e.g., 'Web Server 01')",
    )
    parser.add_argument(
        "--host-id",
        required=True,
        help="Unique host identifier (e.g., 'web01')",
    )
    parser.add_argument(
        "--frequency",
        type=int,
        default=300,
        help="Expected heartbeat frequency in seconds (default: 300 = 5 minutes)",
    )
    parser.add_argument(
        "--schedule",
        choices=["always", "business_hours"],
        default="always",
        help="Monitoring schedule (default: always)",
    )
    parser.add_argument(
        "--grace-period",
        type=int,
        default=60,
        help="Grace period in seconds (default: 60)",
    )
    parser.add_argument(
        "--token",
        help="Authentication token (generates if not provided)",
    )

    args = parser.parse_args()

    print(f"Registering host '{args.name}' ({args.host_id})...")

    result, token = register_host(
        server_url=args.server,
        name=args.name,
        host_id=args.host_id,
        frequency=args.frequency,
        token=args.token,
        schedule_type=args.schedule,
        grace_period=args.grace_period,
    )

    print("\n✅ Host registered successfully!")
    print(f"\nHost ID: {result['host_id']}")
    print(f"Name: {result['name']}")
    print(f"Heartbeat URL: {result['heartbeat_url']}")
    print(f"Token: {token}")
    print(f"Expected frequency: {result['expected_frequency_seconds']}s ({result['expected_frequency_seconds'] // 60} minutes)")
    print(f"Schedule: {result['schedule_type']}")

    print("\n" + "="*80)
    print("CLIENT SETUP INSTRUCTIONS")
    print("="*80)

    print(f"\n1. Save the following token securely on the client host:")
    print(f"   TOKEN={token}")

    print(f"\n2. Download the heartbeat script:")
    print(f"   curl -O {args.server}/scripts/client-heartbeat.sh")
    print(f"   chmod +x client-heartbeat.sh")

    print(f"\n3. Test the heartbeat manually:")
    print(f"   ./client-heartbeat.sh {args.host_id} {token} {args.server}")

    cron_minutes = max(1, args.frequency // 60)
    print(f"\n4. Set up cron job (every {cron_minutes} minute(s)):")
    print(f"   */{cron_minutes} * * * * /path/to/client-heartbeat.sh {args.host_id} {token} {args.server}")

    print(f"\n5. Alternatively, use curl directly:")
    print(f"   curl -X POST {result['heartbeat_url']} \\")
    print(f"        -H 'Authorization: Bearer {token}'")

    print("\n" + "="*80)
    print(f"\nMonitor the dashboard at: {args.server}/api/v1/dashboard")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
