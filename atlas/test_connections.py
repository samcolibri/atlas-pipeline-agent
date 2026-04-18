"""
ATLAS — Connection Test Script
Run this to verify all API integrations are working.
Usage: python atlas/test_connections.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_salesforce():
    """Test: Can we connect to Salesforce and read data?"""
    from simple_salesforce import Salesforce

    sf = Salesforce(
        username=os.getenv("SF_USERNAME"),
        password=os.getenv("SF_PASSWORD"),
        security_token=os.getenv("SF_SECURITY_TOKEN", ""),
        client_id=os.getenv("SF_CLIENT_ID"),
        domain=os.getenv("SF_DOMAIN", "login"),
    )

    result = sf.query("SELECT COUNT() FROM Lead")
    print(f"  ✅ Salesforce connected. Total leads: {result['totalSize']}")

    closed_lost = sf.query(
        "SELECT COUNT() FROM Opportunity WHERE StageName = 'Closed Lost'"
    )
    print(f"     Closed-lost opps: {closed_lost['totalSize']}")


def test_outreach():
    """Test: Can we connect to Outreach and read sequences?"""
    import requests

    headers = {
        "Authorization": f"Bearer {os.getenv('OUTREACH_ACCESS_TOKEN')}",
        "Content-Type": "application/vnd.api+json",
    }

    resp = requests.get(
        "https://api.outreach.io/api/v2/sequences?page[limit]=5",
        headers=headers,
        timeout=15,
    )

    if resp.status_code == 200:
        sequences = resp.json().get("data", [])
        print(f"  ✅ Outreach connected. Found {len(sequences)} sequences:")
        for seq in sequences:
            name = seq.get("attributes", {}).get("name", "unnamed")
            print(f"     - {name}")
    else:
        print(f"  ❌ Outreach failed: {resp.status_code} — {resp.text[:200]}")


def test_6sense():
    """Test: Can we connect to 6sense and pull intent data?"""
    import requests

    headers = {
        "Authorization": f"Token {os.getenv('SIXSENSE_API_KEY')}",
        "Content-Type": "application/json",
    }

    resp = requests.get(
        "https://api.6sense.com/v3/company/search",
        headers=headers,
        json={
            "filter": {
                "industry": ["Financial Services"],
                "buying_stage": ["Decision", "Purchase"],
            },
            "limit": 5,
        },
        timeout=15,
    )

    if resp.status_code == 200:
        accounts = resp.json().get("results", [])
        print(f"  ✅ 6sense connected. Top intent accounts:")
        for acc in accounts:
            print(f"     - {acc.get('company', 'unknown')} (intent: {acc.get('intent_score', 'N/A')})")
    else:
        print(f"  ⚠️  6sense returned {resp.status_code} (may need CSV fallback)")


def test_claude():
    """Test: Can we connect to Claude and generate content?"""
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=128,
        messages=[
            {
                "role": "user",
                "content": "In one sentence, why do compliance officers at mid-size banks need better GRC tools? Be specific.",
            }
        ],
    )

    print(f"  ✅ Claude connected. Test generation:")
    print(f"     {message.content[0].text}")


def test_teams():
    """Test: Can we send a Teams alert?"""
    import requests

    resp = requests.post(
        os.getenv("TEAMS_WEBHOOK_URL"),
        json={
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": "ATLAS Test",
            "sections": [
                {
                    "activityTitle": "✅ ATLAS Pipeline Agent — Connection Test",
                    "text": "Test alert from ATLAS. If you see this, Teams integration is working.",
                }
            ],
        },
        timeout=10,
    )

    if resp.status_code == 200:
        print(f"  ✅ Teams connected. Check your channel for the test message.")
    else:
        print(f"  ❌ Teams failed: {resp.status_code}")


def main():
    print()
    print("=" * 60)
    print("  ATLAS — CONNECTION TEST")
    print("=" * 60)
    print()

    tests = [
        ("Salesforce", "SF_CLIENT_ID", test_salesforce),
        ("Outreach", "OUTREACH_ACCESS_TOKEN", test_outreach),
        ("6sense", "SIXSENSE_API_KEY", test_6sense),
        ("Claude", "ANTHROPIC_API_KEY", test_claude),
        ("Teams", "TEAMS_WEBHOOK_URL", test_teams),
    ]

    configured = 0
    passed = 0

    for name, env_var, test_fn in tests:
        print(f"  {name}:")
        if not os.getenv(env_var):
            print(f"  ⬚  Not configured (set {env_var})")
        else:
            configured += 1
            try:
                test_fn()
                passed += 1
            except Exception as e:
                print(f"  ❌ Error: {e}")
        print()

    print("=" * 60)
    print(f"  RESULTS: {passed}/{configured} configured APIs passed ({5 - configured} not configured)")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
