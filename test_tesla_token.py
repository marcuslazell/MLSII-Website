import os
from dotenv import load_dotenv
import teslapy

load_dotenv()

def test_tesla_connection():
    email = os.getenv('TESLA_EMAIL')
    refresh_token = os.getenv('TESLA_REFRESH_TOKEN')
    
    print(f"Testing Tesla API connection...")
    print(f"Email: {email}")
    print(f"Refresh token length: {len(refresh_token) if refresh_token else 0}")
    
    try:
        with teslapy.Tesla(email) as tesla:
            tesla.refresh_token = refresh_token
            print("\nAttempting to fetch vehicles...")
            vehicles = tesla.vehicle_list()
            print(f"\nFound {len(vehicles)} vehicles:")
            for v in vehicles:
                print(f"- {v['display_name']}: {v['state']}")
            return True
    except Exception as e:
        print(f"\nError: {str(e)}")
        return False

if __name__ == "__main__":
    test_tesla_connection()