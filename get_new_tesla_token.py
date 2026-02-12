import os
import time
import base64
import hashlib
import secrets
import webbrowser
import getpass
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from dotenv import load_dotenv

AUTH_URL = "https://auth.tesla.com/oauth2/v3/authorize"
TOKEN_URL = "https://auth.tesla.com/oauth2/v3/token"
DEFAULT_SCOPES = "openid offline_access user_data vehicle_device_data"


def update_env_values(path, updates):
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    seen = set()
    new_lines = []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                seen.add(key)
                continue
        new_lines.append(line)

    for key, value in updates.items():
        if key not in seen:
            new_lines.append(f"{key}={value}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def make_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode("ascii")
    challenge = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(challenge).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def get_new_tesla_token():
    """Get fresh Tesla Fleet OAuth tokens for this app and store them in .env."""
    load_dotenv(interpolate=False)

    client_id = os.getenv("TESLA_CLIENT_ID")
    client_secret = os.getenv("TESLA_CLIENT_SECRET")
    fleet_base = os.getenv("TESLA_FLEET_BASE_URL", "https://fleet-api.prd.na.vn.cloud.tesla.com")
    redirect_uri = os.getenv("TESLA_REDIRECT_URI")

    if not client_id:
        raise ValueError("TESLA_CLIENT_ID is missing in .env")
    if not redirect_uri:
        raise ValueError("TESLA_REDIRECT_URI is missing in .env")

    code_verifier, code_challenge = make_pkce_pair()
    state = secrets.token_urlsafe(16)
    query = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": DEFAULT_SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    login_url = f"{AUTH_URL}?{urlencode(query)}"

    print("\nTesla Fleet OAuth setup")
    print("1) Login in the opened browser window")
    print("2) After redirect, copy the FULL callback URL and paste it here\n")
    print(f"Redirect URI (must exactly match Tesla app config): {redirect_uri}")
    print(f"Requested scopes: {DEFAULT_SCOPES}\n")
    print("Opening browser...")
    webbrowser.open(login_url)

    callback_url = input("\nPaste callback URL: ").strip()
    parsed = urlparse(callback_url)
    params = parse_qs(parsed.query)
    if "error" in params:
        raise ValueError(f"OAuth error: {params.get('error', ['unknown'])[0]}")
    code = params.get("code", [None])[0]
    returned_state = params.get("state", [None])[0]
    if not code:
        if "/oauth2/v3/authorize" in callback_url:
            raise ValueError(
                "You pasted the authorize URL, not the callback URL. "
                "Complete login and paste the redirected URL from your configured redirect URI page."
            )
        raise ValueError(
            "No authorization code found in callback URL. "
            "Ensure TESLA_REDIRECT_URI exactly matches the Allowed Redirect URI in Tesla Developer."
        )
    if returned_state != state:
        raise ValueError("State mismatch; aborting")

    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
        "audience": fleet_base,
    }
    if client_secret:
        payload["client_secret"] = client_secret

    resp = requests.post(TOKEN_URL, data=payload, timeout=20)
    if not resp.ok and "client_secret mismatch" in resp.text.lower():
        print("\nTesla rejected the current client secret.")
        print("Paste the CURRENT Client Secret from Tesla Developer App Details.")
        fresh_secret = getpass.getpass("Client secret: ").strip()
        if not fresh_secret:
            raise ValueError("Client secret is required")
        payload["client_secret"] = fresh_secret
        resp = requests.post(TOKEN_URL, data=payload, timeout=20)
        if resp.ok:
            client_secret = fresh_secret
        else:
            raise ValueError(f"Token exchange failed ({resp.status_code}): {resp.text[:400]}")
    elif not resp.ok:
        raise ValueError(f"Token exchange failed ({resp.status_code}): {resp.text[:400]}")
    token_data = resp.json()

    refresh_token = token_data.get("refresh_token")
    access_token = token_data.get("access_token")
    expires_in = int(token_data.get("expires_in", 0))
    if not refresh_token or not access_token:
        raise ValueError("Token response missing refresh/access token")

    updates = {
        "TESLA_CLIENT_SECRET": client_secret or "",
        "TESLA_REFRESH_TOKEN": refresh_token,
        "TESLA_ACCESS_TOKEN": access_token,
        "TESLA_EXPIRES_IN": str(expires_in),
        "TESLA_EXPIRES_AT": str(int(time.time()) + expires_in),
    }
    update_env_values(".env", updates)

    print("\nSuccess: Tesla tokens updated in .env")
    print(f"Refresh token length: {len(refresh_token)}")
    print(f"Access token length: {len(access_token)}")
    print("Restart your Flask app after this.")

if __name__ == "__main__":
    get_new_tesla_token()
