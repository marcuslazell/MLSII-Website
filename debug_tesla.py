import os
from dotenv import load_dotenv
import teslapy

def debug_tesla_connection():
    load_dotenv()
    email = os.getenv('TESLA_EMAIL')
    refresh_token = os.getenv('TESLA_REFRESH_TOKEN')
    
    try:
        tesla = teslapy.Tesla(email)
        tesla.token = {
            'refresh_token': refresh_token,
            'token_type': 'Bearer'
        }
        tesla.fetch_token()
        
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
    debug_tesla_connection()