import requests
import time
import concurrent.futures
from typing import List, Dict

def simulate_brute_force(url: str, username: str, password_list: List[str]) -> None:
    print(f"Simulating brute force attack on user: {username}")
    start_time = time.time()
    
    for attempt, password in enumerate(password_list, 1):
        try:
            response = requests.post(url, data={"username": username, "password": password})
            print(f"Attempt {attempt}: Status code: {response.status_code}, Response: {response.text[:100]}...")
            
            if response.status_code == 200 and "<!DOCTYPE html>" in response.text:
                print(f"Success: Password found after {attempt} attempts.")
                print(f"Time taken: {time.time() - start_time:.2f} seconds")
                return
        except requests.RequestException as e:
            print(f"Request failed: {e}")
        
        time.sleep(0.5)  # Delay to avoid overwhelming the server
    
    print(f"Attack failed. Attempting {len(password_list)} passwords in {time.time() - start_time:.2f} seconds.")

def send_request(url: str, session: requests.Session) -> int:
    try:
        response = session.get(url)
        return response.status_code
    except requests.RequestException:
        return 0

def simulate_dos(url: str, num_requests: int, max_workers: int = 10) -> None:
    print(f"Simulating DoS attack with {num_requests} requests")
    start_time = time.time()
    results: Dict[int, int] = {200: 0, 0: 0}  # 0 represents failed requests

    with requests.Session() as session:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(send_request, url, session) for _ in range(num_requests)]
            for future in concurrent.futures.as_completed(futures):
                status_code = future.result()
                results[status_code] = results.get(status_code, 0) + 1
                print(f"Request completed with status: {status_code}")

    end_time = time.time()
    total_time = end_time - start_time
    requests_per_second = num_requests / total_time

    print(f"\nDoS simulation completed in {total_time:.2f} seconds")
    print(f"Successful requests: {results[200]}")
    print(f"Failed requests: {results[0]}")
    print(f"Requests per second: {requests_per_second:.2f}")

def simulate_api_injection(url: str) -> None:
    print("Simulating API Injection attacks")

    test_cases = [
        ("Normal data", {
            "username": "normaluser",
            "password": "normalpass",
            "email": "normal@example.com",
            "role": "student",
            "year_group": 9
        }),
        ("SQL Injection attempt", {
            "username": "admin' --",
            "password": "doesn't matter",
            "email": "hacker@example.com",
            "role": "student",
            "year_group": 9
        }),
        ("XSS attempt", {
            "username": "<script>alert('XSS')</script>",
            "password": "xsspass",
            "email": "xss@example.com",
            "role": "student",
            "year_group": 9
        }),
        ("Role escalation attempt", {
            "username": "hackerman",
            "password": "hackpass",
            "email": "hack@example.com",
            "role": "admin",  # Attempting to register as admin
            "year_group": 9
        })
    ]

    for case_name, data in test_cases:
        print(f"\nTesting: {case_name}")
        try:
            response = requests.post(url, json=data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:100]}...")  # Print first 100 characters of response
        except requests.RequestException as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    base_url = "http://localhost:8000"
    
    print("Running Brute Force Simulation:")
    simulate_brute_force(f"{base_url}/login", "admin", ["wrong1", "wrong2", "adminpass"])
    
    print("\nRunning DoS Simulation:")
    simulate_dos(base_url, 50)  # Simulating with 50 requests

    print("\nRunning API Injection Simulation:")
    simulate_api_injection(f"{base_url}/register")
