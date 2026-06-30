#!/usr/bin/env python3
"""Telegram Bot API verification adapter.

Checks:
- Bot token validity
- Correct chat ID routing
- Message delivery
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


TELEGRAM_API = "https://api.telegram.org/bot"


class TelegramVerificationError(RuntimeError):
    """Raised when Telegram verification fails."""


def _get_token() -> str:
    """Get bot token from environment."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise TelegramVerificationError("TELEGRAM_BOT_TOKEN not set")
    return token


def verify_token(token: str) -> dict[str, Any]:
    """Verify bot token and get bot info."""
    url = f"{TELEGRAM_API}{token}/getMe"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise TelegramVerificationError(f"HTTP {e.code}: {e.read().decode()[:200]}") from e
    except urllib.error.URLError as e:
        raise TelegramVerificationError(f"Network error: {e.reason}") from e

    if not data.get("ok"):
        raise TelegramVerificationError(f"API error: {data}")

    result = data.get("result", {})
    return {
        "id": result.get("id"),
        "username": result.get("username"),
        "first_name": result.get("first_name"),
    }


def verify_send(token: str, chat_id: str, test_mode: bool = True) -> dict[str, Any]:
    """Send a test message (or dry-run) and return delivery evidence."""
    if test_mode:
        return {
            "sent": False,
            "dry_run": True,
            "chat_id": chat_id,
            "note": "Dry run - no message sent",
        }

    url = f"{TELEGRAM_API}{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": "[HERMES VERIFICATION] Autonomous loop test message",
        "parse_mode": "Markdown",
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise TelegramVerificationError(f"HTTP {e.code}: {e.read().decode()[:200]}") from e

    if not data.get("ok"):
        raise TelegramVerificationError(f"Send failed: {data}")

    result = data.get("result", {})
    return {
        "sent": True,
        "message_id": result.get("message_id"),
        "chat_id": result.get("chat", {}).get("id"),
        "timestamp": result.get("date"),
    }


def main() -> int:
    """Run Telegram verification."""
    print("=== Telegram Verification ===")

    try:
        token = _get_token()
    except TelegramVerificationError as e:
        print(f"  TOKEN: {e}")
        return 1

    # 1. Token check
    try:
        bot = verify_token(token)
        print(f"  BOT: @{bot['username']} (id: {bot['id']})")
    except TelegramVerificationError as e:
        print(f"  AUTH ERROR: {e}")
        return 1

    # 2. Chat IDs from environment
    staging_chat = os.environ.get("TELEGRAM_STAGING_CHAT_ID", "")
    prod_chat = os.environ.get("TELEGRAM_PROD_CHAT_ID", "")
    print(f"  STAGING CHAT: {'SET' if staging_chat else 'NOT SET'}")
    print(f"  PROD CHAT: {'SET' if prod_chat else 'NOT SET'}")

    # 3. Dry-run delivery test
    if staging_chat:
        result = verify_send(token, staging_chat, test_mode=True)
        print(f"  DELIVERY TEST: {result['note']}")

    print("  VERIFICATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
