import teslapy
import os
from dotenv import load_dotenv
import json

def get_new_tesla_token():
    """
    Get new Tesla authentication tokens using email/password auth.
    This will ensure we save the actual token value, not a method reference.
    """
    load_dotenv()
    email = os.getenv('TESLA_EMAIL')
    
    print("\nStarting Tesla authentication process...")
    print("This will open your web browser for Tesla login.")
    print("After successful login, the script will save your new refresh token.\n")
    
    try:
        with teslapy.Tesla(email) as tesla:
            tesla.fetch_token()
            
            # Get the token data
            token_data = tesla.token
            if not isinstance(token_data, dict) or 'refresh_token' not in token_data:
                raise ValueError("Failed to get proper token data")
                
            refresh_token = token_data['refresh_token']
            
            # Verify we have a proper token string
            if not isinstance(refresh_token, str) or len(refresh_token) < 100:
                raise ValueError("Invalid refresh token received")
            
            print(f"Retrieved new refresh token (length: {len(refresh_token)})")
            
            # Read existing .env content
            with open('.env', 'r') as file:
                env_lines = file.readlines()
            
            # Update the refresh token line
            refresh_token_line = f'TESLA_REFRESH_TOKEN={refresh_token}\n'
            token_updated = False
            
            for i, line in enumerate(env_lines):
                if line.startswith('TESLA_REFRESH_TOKEN='):
                    env_lines[i] = refresh_token_line
                    token_updated = True
                    break
            
            if not token_updated:
                env_lines.append(refresh_token_line)
            
            # Write back to .env
            with open('.env', 'w') as file:
                file.writelines(env_lines)
            
            print("\nAuthentication successful!")
            print("New refresh token has been saved to your .env file")
            print("\nToken verification:")
            print(f"- Token type: {type(refresh_token)}")
            print(f"- Token length: {len(refresh_token)}")
            print(f"- Token preview: {refresh_token[:50]}...")
            print("\nPlease restart your Flask application to use the new token.")
            
    except Exception as e:
        print(f"\nError during authentication: {str(e)}")
        print("Please try again or check your Tesla account credentials.")
        raise

if __name__ == "__main__":
    get_new_tesla_token()