"""Test SerpAPI integration for image search"""
import os
from dotenv import load_dotenv
from image_search_service import image_search_service

load_dotenv()

print("🔍 Testing SerpAPI Image Search\n")
print(f"SerpAPI Key configured: {bool(os.getenv('SERPAPI_KEY'))}")
print(f"Using SerpAPI: {image_search_service.use_serpapi}\n")

# Test 1: Search for Urea fertilizer
print("1️⃣ Searching for Urea fertilizer images...")
images = image_search_service.search_fertilizer_images("Urea")
print(f"   Found {len(images)} images")
for i, img in enumerate(images[:3], 1):
    print(f"   {i}. {img['title'][:50]}")
    print(f"      URL: {img['url'][:80]}...")

# Test 2: Search for pesticide
print("\n2️⃣ Searching for Chlorpyrifos pesticide images...")
images = image_search_service.search_pesticide_images("Chlorpyrifos")
print(f"   Found {len(images)} images")
for i, img in enumerate(images[:3], 1):
    print(f"   {i}. {img['title'][:50]}")
    print(f"      URL: {img['url'][:80]}...")

# Test 3: Search for crop disease
print("\n3️⃣ Searching for wheat rust disease images...")
images = image_search_service.search_crop_disease_images("rust", "wheat")
print(f"   Found {len(images)} images")
for i, img in enumerate(images[:3], 1):
    print(f"   {i}. {img['title'][:50]}")
    print(f"      URL: {img['url'][:80]}...")

print("\n✅ SerpAPI test complete!")
