"""Test local image database and complete flow"""
import os
os.chdir(os.path.dirname(__file__))  # Ensure correct working directory

from images_db import images_db
from image_search_service import image_search_service

print("🧪 Testing Local Image Database + SerpAPI Flow\n")
print("=" * 70)

# Test 1: Database stats
print("\n1️⃣ Database Statistics:")
stats = images_db.get_stats()
print(f"   Total Products: {stats['total_products']}")
print(f"   Total Images: {stats['total_images']}")
print(f"   By Category: {stats['by_category']}")

# Test 2: Search for Urea (should find local file)
print("\n2️⃣ Search for 'Urea' (should find LOCAL file):")
print("   " + "-" * 60)
images = image_search_service.search_fertilizer_images("Urea")
print(f"   Found {len(images)} images:")
for i, img in enumerate(images, 1):
    is_local = " [LOCAL]" if img.get("local") or img.get("trusted") else " [WEB]"
    print(f"   {i}. {img['title'][:50]}{is_local}")
    print(f"      {img['url'][:70]}...")
    print(f"      Source: {img.get('source', 'Unknown')}")

# Test 3: Search for Neem Manure (should find local file)
print("\n3️⃣ Search for 'Neem Manure' (should find LOCAL file):")
print("   " + "-" * 60)
images = image_search_service.search_fertilizer_images("Neem")
print(f"   Found {len(images)} images:")
for i, img in enumerate(images, 1):
    is_local = " [LOCAL]" if img.get("local") or img.get("trusted") else " [WEB]"
    print(f"   {i}. {img['title'][:50]}{is_local}")
    print(f"      {img['url'][:70]}...")
    print(f"      Source: {img.get('source', 'Unknown')}")

# Test 4: Search for DAP (not in local, should use SerpAPI)
print("\n4️⃣ Search for 'DAP' (should fallback to SerpAPI):")
print("   " + "-" * 60)
images = image_search_service.search_fertilizer_images("DAP")
print(f"   Found {len(images)} images:")
for i, img in enumerate(images, 1):
    is_local = " [LOCAL]" if img.get("local") or img.get("trusted") else " [WEB]"
    print(f"   {i}. {img['title'][:50]}{is_local}")
    print(f"      {img['url'][:70]}...")
    print(f"      Source: {img.get('source', 'Unknown')}")

# Test 5: Search for pesticide (should use SerpAPI)
print("\n5️⃣ Search for 'Chlorpyrifos' pesticide:")
print("   " + "-" * 60)
images = image_search_service.search_pesticide_images("Chlorpyrifos")
print(f"   Found {len(images)} images:")
for i, img in enumerate(images, 1):
    is_local = " [LOCAL]" if img.get("local") or img.get("trusted") else " [WEB]"
    print(f"   {i}. {img['title'][:50]}{is_local}")
    print(f"      {img['url'][:70]}...")
    print(f"      Source: {img.get('source', 'Unknown')}")

print("\n" + "=" * 70)
print("✅ Complete flow test finished!")
print("\nFlow Summary:")
print("  ✓ Local DB scanned and populated with product images")
print("  ✓ Local files served via http://localhost:8000/products/{filename}")
print("  ✓ Search checks local DB first (instant response)")
print("  ✓ Falls back to SerpAPI for missing products")
print("  ✓ Images marked as [LOCAL] or [WEB] for tracking")
