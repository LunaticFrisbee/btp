# tester.py
import requests
import time
from colorama import Fore, Style

# Configuration
API_URL = 'http://127.0.0.1:5000/api/data'  # Adjust the URL if necessary
TEST_IP = '127.0.0.1'  # The IP address to test from
MAX_REQUESTS = 12  # Number of requests to send

def test_rate_limiting():
    for i in range(MAX_REQUESTS):
        try:
            response = requests.get(API_URL, headers={'X-Forwarded-For': TEST_IP})
            if response.status_code == 200:
                print(f"{Fore.GREEN}Request {i + 1}: {response.status_code} - {response.json()}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Server is handling requests...{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Request {i + 1}: {response.status_code} - Unable to reach server now.{Style.RESET_ALL}")
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}Request {i + 1}: Error - {str(e)}{Style.RESET_ALL}")
        
        time.sleep(3)  # Wait 5 seconds between requests

if __name__ == '__main__':
    test_rate_limiting()