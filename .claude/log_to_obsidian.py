#!/usr/bin/env python3
"""
Dev activity logger → Obsidian daily note
Usage: python log_to_obsidian.py "your activity message" --tag speckit
"""

import argparse
import json
import os
import ssl
import urllib.request
from datetime import datetime

API_KEY = os.environ.get("OBSIDIAN_API_KEY", "")  # set in your .env

def get_daily_note_path() -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return f"Daily Notes/{today}.md"

def append_to_daily_note(message: str, tag: str, source: str):
    timestamp = datetime.now().strftime("%H:%M")
    today = datetime.now().strftime("%Y-%m-%d")

    # Format the log entry
    tag_map = {
        "speckit":    "📋",
        "claude":     "🤖",
        "git":        "🔀",
        "test":       "🧪",
        "deploy":     "🚀",
        "general":    "📝",
    }
    icon = tag_map.get(tag, "📝")
    
    entry = f"\n- {icon} `{timestamp}` **[{tag.upper()}]** {message}"
    if source:
        entry += f" _(via {source})_"

    note_path = get_daily_note_path()

    # Check if daily note exists, create header if not
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    # Try to get existing note
    try:
        req = urllib.request.Request(
            f"{OBSIDIAN_API}/vault/{note_path}",
            headers=headers
        )
        with urllib.request.urlopen(req, context=ctx) as r:
            existing = r.read().decode()
    except urllib.error.HTTPError:
        # Note doesn't exist yet — create with header
        existing = f"# Dev Log — {today}\n\n## Activity\n"

    updated = existing + entry

    # Write back
    data = json.dumps({"content": updated}).encode()
    req = urllib.request.Request(
        f"{OBSIDIAN_API}/vault/{note_path}",
        data=data,
        headers={**headers, "Content-Type": "application/json"},
        method="PUT"
    )
    urllib.request.urlopen(req, context=ctx)
    print(f"✅ Logged to Obsidian: {entry.strip()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("message", help="Activity to log")
    parser.add_argument("--tag", default="general",
                        choices=["speckit","claude","git","test","deploy","general"])
    parser.add_argument("--source", default="", help="Source tool/agent")
    args = parser.parse_args()
    append_to_daily_note(args.message, args.tag, args.source)