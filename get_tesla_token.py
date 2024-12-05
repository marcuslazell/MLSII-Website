import requests
import json

def get_tesla_token():
    auth_url = "https://auth.tesla.com/oauth2/v3/token"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "grant_type": "password",
        "client_id": "ownerapi",
        "client_secret": os.getenv('TESLA_CLIENT_SECRET'),
        "email": os.getenv('TESLA_EMAIL'),
        "password": os.getenv('TESLA_PASSWORD')
    }

    print("Getting new Tesla token...")
    try:
        response = requests.post(auth_url, headers=headers, json=data)
        if response.status_code == 200:
            token_data = response.json()
            print("\nAuthentication successful!")
            print("\nAdd this to your .env file:")
            print("--------------------------------")
            print(f"TESLA_ACCESS_TOKEN={token_data['access_token']}")
            
            # Save full response to file
            with open('tesla_tokens.json', 'w') as f:
                json.dump(token_data, f, indent=4)
            print("\nFull token data saved to tesla_tokens.json")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    get_tesla_token()