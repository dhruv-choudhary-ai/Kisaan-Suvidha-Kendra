import requests

BASE_URL = "http://localhost:8000"  # Change to your actual base URL

def test_endpoint(path, method="GET", data=None, expected_status=200):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"Unsupported method: {method}")
            return False
        if response.status_code == expected_status:
            print(f"PASS: {method} {path} [{response.status_code}]")
            return True
        else:
            print(f"FAIL: {method} {path} [{response.status_code}] - {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {method} {path} - {e}")
        return False

def main():
    # Add all your endpoints here
    endpoints = [
        { "path": "/endpoint1", "method": "GET", "expected_status": 200 },
        { "path": "/endpoint2", "method": "POST", "data": {"key": "value"}, "expected_status": 201 },
        # Add more endpoints as needed
    ]
    all_passed = True
    for ep in endpoints:
        result = test_endpoint(
            ep["path"],
            method=ep.get("method", "GET"),
            data=ep.get("data"),
            expected_status=ep.get("expected_status", 200)
        )
        if not result:
            all_passed = False
    if all_passed:
        print("All endpoints passed!")
    else:
        print("Some endpoints failed.")

if __name__ == "__main__":
    main()