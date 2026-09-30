#!/usr/bin/env python3

import os
import json
import requests

from google.oauth2 import service_account
from google.auth.transport.requests import Request


INDEXING_ENDPOINT = (
    "https://indexing.googleapis.com/v3/urlNotifications:publish"
)

SCOPE = "https://www.googleapis.com/auth/indexing"


def main():

    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    if not raw:
        raise SystemExit(
            "Missing GOOGLE_SERVICE_ACCOUNT_JSON secret"
        )

    changes_file = ".seo-changes.json"

    if not os.path.exists(changes_file):
        print("No .seo-changes.json found. Nothing to notify.")
        return

    with open(changes_file, "r", encoding="utf-8") as f:
        changes = json.load(f)

    changed = changes.get("changed", [])
    removed = changes.get("removed", [])

    if not changed and not removed:
        print("No URL changes to notify.")
        return

    credentials = service_account.Credentials.from_service_account_info(
        json.loads(raw),
        scopes=[SCOPE]
    )

    credentials.refresh(Request())

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }

    sent = 0
    failed = 0

    # Notify Google about updated URLs
    for url in changed[:200]:

        payload = {
            "url": url,
            "type": "URL_UPDATED"
        }

        response = requests.post(
            INDEXING_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.ok:
            sent += 1
            print("UPDATED:", url)
        else:
            failed += 1
            print(
                "FAILED:",
                url,
                response.status_code,
                response.text[:500]
            )

    # Notify Google about removed/expired URLs
    for url in removed[:200]:

        payload = {
            "url": url,
            "type": "URL_DELETED"
        }

        response = requests.post(
            INDEXING_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.ok:
            sent += 1
            print("DELETED:", url)
        else:
            failed += 1
            print(
                "FAILED DELETE:",
                url,
                response.status_code,
                response.text[:500]
            )

    print(
        f"Google Indexing notifications complete. "
        f"Sent: {sent}, Failed: {failed}"
    )


if __name__ == "__main__":
    main()
