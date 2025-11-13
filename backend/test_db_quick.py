from images_db import images_db

stats = images_db.get_stats()
print(f"Products: {stats['total_products']}, Images: {stats['total_images']}")
print(f"Categories: {stats['by_category']}")

print("\nSearching for 'Urea':")
results = images_db.search_images('Urea')
for img in results[:3]:
    local_tag = "[LOCAL]" if img.get('local') else "[WEB]"
    print(f"  {local_tag} {img['title']}")
    print(f"       {img['url'][:70]}")

print("\nSearching for 'Neem':")
results = images_db.search_images('Neem')
for img in results[:2]:
    local_tag = "[LOCAL]" if img.get('local') else "[WEB]"
    print(f"  {local_tag} {img['title']}")
    print(f"       {img['url'][:70]}")
