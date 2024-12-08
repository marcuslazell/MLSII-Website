import os
from dotenv import load_dotenv
import teslapy

def verify_tesla():
    load_dotenv()
    email = os.getenv('TESLA_EMAIL')
    refresh_token = os.getenv('TESLA_REFRESH_TOKEN')

    print("Verifying Tesla connection...")
    print(f"Email: {email}")
    print(f"Token length: {len(refresh_token)}")

    try:
        tesla = teslapy.Tesla(email)
        tesla.token = {
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
        tesla.fetch_token()
        
        print("\nToken refresh successful!")
        vehicles = tesla.vehicle_list()
        print(f"\nFound {len(vehicles)} vehicles:")
        for v in vehicles:
            print(f"- {v['display_name']}: {v['state']}")
        
        tesla.close()
        return True
    except Exception as e:
        print(f"\nError: {str(e)}")
        return False

if __name__ == "__main__":
    verify_tesla()