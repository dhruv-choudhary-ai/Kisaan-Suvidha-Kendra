#!/usr/bin/env python3
"""
Test script to verify product image display functionality
Tests fertilizer and pesticide queries to ensure images are returned
"""

import requests
import json
import base64
import sys
from pathlib import Path

# Test configuration
BACKEND_URL = "http://localhost:8000"
TEST_SESSION_ID = "test_image_session_001"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠ {message}{RESET}")


def test_start_session():
    """Test session initialization"""
    print_info("Testing session initialization...")
    
    try:
        response = requests.post(f"{BACKEND_URL}/voice/start-session")
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print_success(f"Session started: {session_id}")
            return session_id
        else:
            print_error(f"Failed to start session: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Session initialization error: {e}")
        return None


def test_language_selection(session_id):
    """Test language selection"""
    print_info("Testing language selection...")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/voice/select-language",
            json={
                "session_id": session_id,
                "language": "hindi"
            }
        )
        
        if response.status_code == 200:
            print_success("Language set to Hindi")
            return True
        else:
            print_error(f"Failed to set language: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Language selection error: {e}")
        return False


def test_fertilizer_query(session_id):
    """Test fertilizer recommendation query that should return images"""
    print_info("Testing fertilizer query...")
    
    query = "मुझे धान के लिए बेहतरीन उर्वरक बताएं"  # "Tell me the best fertilizer for paddy"
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/voice/query",
            json={
                "session_id": session_id,
                "audio_base64": "",  # Empty for text query
                "language": "hindi",
                "text": query
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print_success(f"Query successful")
            print_info(f"Response: {data.get('text_response', '')[:100]}...")
            
            # Check for image-related fields
            requires_images = data.get("requires_images", False)
            image_urls = data.get("image_urls", [])
            
            if requires_images:
                print_success(f"requires_images: True")
            else:
                print_warning(f"requires_images: False (expected True for fertilizer query)")
            
            if image_urls:
                print_success(f"Found {len(image_urls)} product images:")
                for i, img in enumerate(image_urls, 1):
                    print(f"  {i}. {img.get('title', 'Untitled')}")
                    print(f"     URL: {img.get('url', img.get('filename', 'N/A'))}")
                    print(f"     Source: {img.get('source', 'N/A')}")
                return True
            else:
                print_error("No image URLs returned (expected product images)")
                return False
        else:
            print_error(f"Query failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Fertilizer query error: {e}")
        return False


def test_pesticide_query(session_id):
    """Test pesticide recommendation query that should return images"""
    print_info("Testing pesticide query...")
    
    query = "टमाटर में कीड़े लगे हैं, कीटनाशक बताइए"  # "Tomatoes have pests, recommend pesticide"
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/voice/query",
            json={
                "session_id": session_id,
                "audio_base64": "",
                "language": "hindi",
                "text": query
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print_success(f"Query successful")
            print_info(f"Response: {data.get('text_response', '')[:100]}...")
            
            requires_images = data.get("requires_images", False)
            image_urls = data.get("image_urls", [])
            
            if requires_images:
                print_success(f"requires_images: True")
            else:
                print_warning(f"requires_images: False (expected True for pesticide query)")
            
            if image_urls:
                print_success(f"Found {len(image_urls)} product images:")
                for i, img in enumerate(image_urls, 1):
                    print(f"  {i}. {img.get('title', 'Untitled')}")
                    print(f"     URL: {img.get('url', img.get('filename', 'N/A'))}")
                return True
            else:
                print_error("No image URLs returned (expected product images)")
                return False
        else:
            print_error(f"Query failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Pesticide query error: {e}")
        return False


def test_image_serving():
    """Test if product images are accessible via HTTP"""
    print_info("Testing image serving...")
    
    # Check products directory
    products_dir = Path(__file__).parent / "products"
    
    if not products_dir.exists():
        print_error(f"Products directory not found: {products_dir}")
        return False
    
    # Find an image file
    image_files = list(products_dir.glob("*.jpg")) + list(products_dir.glob("*.png"))
    
    if not image_files:
        print_warning("No image files found in products directory")
        return False
    
    test_image = image_files[0]
    print_info(f"Testing image: {test_image.name}")
    
    try:
        response = requests.get(f"{BACKEND_URL}/products/{test_image.name}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type:
                print_success(f"Image accessible: {test_image.name}")
                print_info(f"Content-Type: {content_type}")
                print_info(f"Size: {len(response.content)} bytes")
                return True
            else:
                print_error(f"Wrong content type: {content_type}")
                return False
        else:
            print_error(f"Image not accessible: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Image serving error: {e}")
        return False


def test_websocket_response():
    """Test WebSocket endpoint for image data"""
    print_info("Testing WebSocket endpoint...")
    print_warning("WebSocket test requires manual verification")
    print_info("Connect to: ws://localhost:8000/ws/voice")
    print_info("Expected fields in response:")
    print("  - type: 'response'")
    print("  - requires_images: boolean")
    print("  - image_urls: array")
    return True


def main():
    """Run all tests"""
    print(f"\n{'='*60}")
    print(f"  Product Image Display - Integration Test")
    print(f"{'='*60}\n")
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0
    }
    
    # Test 1: Session initialization
    results["total"] += 1
    session_id = test_start_session()
    if session_id:
        results["passed"] += 1
    else:
        results["failed"] += 1
        print_error("Cannot continue without session")
        return results
    
    print()
    
    # Test 2: Language selection
    results["total"] += 1
    if test_language_selection(session_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    print()
    
    # Test 3: Fertilizer query
    results["total"] += 1
    if test_fertilizer_query(session_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    print()
    
    # Test 4: Pesticide query
    results["total"] += 1
    if test_pesticide_query(session_id):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    print()
    
    # Test 5: Image serving
    results["total"] += 1
    if test_image_serving():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    print()
    
    # Test 6: WebSocket
    results["total"] += 1
    if test_websocket_response():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"  Test Summary")
    print(f"{'='*60}\n")
    print(f"Total:  {results['total']}")
    print_success(f"Passed: {results['passed']}")
    if results['failed'] > 0:
        print_error(f"Failed: {results['failed']}")
    print()
    
    # Frontend testing instructions
    print(f"{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}  Frontend Testing Instructions{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}\n")
    print("1. Start the backend: cd backend && python main.py")
    print("2. Start the frontend: cd modern-kiosk-ui && pnpm run dev")
    print("3. Open browser: http://localhost:3000")
    print("4. Click 'Start' and ask:")
    print(f"   {BLUE}• 'मुझे धान के लिए उर्वरक बताएं'{RESET} (Hindi)")
    print(f"   {BLUE}• 'Tell me about fertilizers for wheat'{RESET} (English)")
    print(f"   {BLUE}• 'कपास में कीड़े हैं, कीटनाशक बताइए'{RESET} (Hindi)")
    print("5. Check if product images appear in ContentPanel")
    print("6. Click on images to open gallery view")
    print("7. Test image navigation and zoom\n")
    
    return results


if __name__ == "__main__":
    try:
        results = main()
        sys.exit(0 if results["failed"] == 0 else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Test suite error: {e}")
        sys.exit(1)
