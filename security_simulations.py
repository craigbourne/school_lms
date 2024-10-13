import warnings
import urllib3
import requests
import time
from contextlib import contextmanager

@contextmanager
def suppress_urllib3_warnings():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=urllib3.exceptions.NotOpenSSLWarning)
        yield

def simulate_brute_force(url, username, password_list):
    print(f"Simulating brute force attack on user: {username}")
    attempts = 0
    start_time = time.time()
    
    for password in password_list:
        attempts += 1
        try:
            response = requests.post(url, data={"username": username, "password": password})
            print(f"Attempt {attempts}: Status code: {response.status_code}, Response: {response.text[:100]}...")
            
            if response.status_code == 200 and "<!DOCTYPE html>" in response.text:
                end_time = time.time()
                print(f"Success: Password found after {attempts} attempts.")
                print(f"Time taken: {end_time - start_time:.2f} seconds")
                return
        except requests.RequestException as e:
            print(f"Request failed: {e}")
        
        time.sleep(0.5)  # Delay to avoid overwhelming the server
    
    print(f"Attack failed. Tried {attempts} passwords in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    base_url = "http://localhost:8000"
    
    print("Running Brute Force Simulation:")
    simulate_brute_force(f"{base_url}/login", "admin", ["wrong1", "wrong2", "adminpass"])