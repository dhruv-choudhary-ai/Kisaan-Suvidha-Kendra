from image_search_service import image_search_service

print("Test: search_fertilizer_images('Urea')")
imgs = image_search_service.search_fertilizer_images('Urea')
print(f"Found {len(imgs)} images")
for i, img in enumerate(imgs, 1):
    print(f"{i}. {img.get('title')} - {img.get('url')}")

print('\nTest: search_pesticide_images("Chlorpyrifos")')
imgs = image_search_service.search_pesticide_images('Chlorpyrifos')
print(f"Found {len(imgs)} images")
for i, img in enumerate(imgs, 1):
    print(f"{i}. {img.get('title')} - {img.get('url')}")

print('\nTest: search_crop_disease_images("rust","wheat")')
imgs = image_search_service.search_crop_disease_images('rust', 'wheat')
print(f"Found {len(imgs)} images")
for i, img in enumerate(imgs, 1):
    print(f"{i}. {img.get('title')} - {img.get('url')}")
