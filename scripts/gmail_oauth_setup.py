from __future__ import annotations

import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow


GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def main() -> None:
    client_secret_path = os.environ.get("GMAIL_OAUTH_CLIENT_SECRET_PATH", "").strip()
    token_path = os.environ.get("GMAIL_TOKEN_PATH", "").strip()

    if not client_secret_path:
        raise SystemExit("GMAIL_OAUTH_CLIENT_SECRET_PATH is required.")
    if not token_path:
        raise SystemExit("GMAIL_TOKEN_PATH is required.")

    token_file = Path(token_path)
    token_file.parent.mkdir(parents=True, exist_ok=True)

    flow = InstalledAppFlow.from_client_secrets_file(
        client_secret_path,
        scopes=[GMAIL_READONLY_SCOPE],
    )
    credentials = flow.run_local_server(port=0)
    token_file.write_text(credentials.to_json(), encoding="utf-8")
    print(f"Saved Gmail OAuth token to {token_file}")


if __name__ == "__main__":
    main()
