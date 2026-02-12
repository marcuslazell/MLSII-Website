import os
import requests
from dotenv import load_dotenv


AUTH_TOKEN_URL = "https://auth.tesla.com/oauth2/v3/token"


def register_partner():
    load_dotenv(interpolate=False)

    client_id = os.getenv("TESLA_CLIENT_ID")
    client_secret = os.getenv("TESLA_CLIENT_SECRET")
    fleet_base = os.getenv("TESLA_FLEET_BASE_URL", "https://fleet-api.prd.na.vn.cloud.tesla.com")
    partner_domain = os.getenv("TESLA_PARTNER_DOMAIN", "www.marcuslshaw.com")

    if not client_id or not client_secret:
        raise ValueError("TESLA_CLIENT_ID and TESLA_CLIENT_SECRET are required")

    token_resp = requests.post(
        AUTH_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": fleet_base,
        },
        timeout=20,
    )
    token_resp.raise_for_status()
    access_token = token_resp.json().get("access_token")
    if not access_token:
        raise ValueError("Failed to obtain partner access token")

    register_resp = requests.post(
        f"{fleet_base}/api/1/partner_accounts",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"domain": partner_domain},
        timeout=20,
    )

    print("register status:", register_resp.status_code)
    print(register_resp.text[:1000])
    register_resp.raise_for_status()

    print("\nPartner registration complete.")


if __name__ == "__main__":
    register_partner()
