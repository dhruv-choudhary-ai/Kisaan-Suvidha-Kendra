"""
Image Search Service for Kisaan Suvidha Kendra
Fetches relevant images for agricultural products, diseases, crops, and equipment
Supports multiple search providers: DuckDuckGo (free), SerpAPI (premium)
"""

import os
import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional
from dotenv import load_dotenv
import json
from urllib.parse import quote_plus
import requests

logger = logging.getLogger(__name__)
load_dotenv()

# Import local image database
from images_db import images_db

class ImageSearchService:
    """Service for searching and retrieving agricultural images"""
    
    def __init__(self):
        self.serpapi_key = os.getenv("SERPAPI_KEY")
        self.use_serpapi = bool(self.serpapi_key)
        self.max_images = int(os.getenv("MAX_IMAGES_PER_RESPONSE", "4"))
        self.images_per_query = int(os.getenv("IMAGES_PER_QUERY", "2"))
        self.timeout = int(os.getenv("IMAGE_SEARCH_TIMEOUT", "5"))
        
        logger.info(f"Image Search Service initialized. Using: {'SerpAPI' if self.use_serpapi else 'DuckDuckGo'}")
    
    
    def search_images(self, query: str, num_images: int = None) -> List[Dict[str, str]]:
        """
        Search for images using local database first, then SerpAPI as fallback
        
        Args:
            query: Search query string
            num_images: Number of images to retrieve (default from config)
            
        Returns:
            List of image dictionaries with url, title, source
        """
        if num_images is None:
            num_images = self.images_per_query
        
        # STEP 1: Check local database first
        logger.info(f"Searching local database for: {query}")
        local_images = images_db.search_images(query, limit=num_images)
        
        if local_images and len(local_images) >= num_images:
            logger.info(f"Found {len(local_images)} images in local DB (sufficient)")
            return local_images
        
        # STEP 2: If not enough in local DB, use SerpAPI as fallback
        logger.info(f"Local DB returned {len(local_images)} images, using SerpAPI for more")
        
        try:
            if self.use_serpapi:
                results = self._search_serpapi(query, num_images - len(local_images))
            else:
                results = self._search_duckduckgo(query, num_images - len(local_images))

            # Combine local + API results
            all_results = local_images + results
            
            # If still no results, use placeholders
            if not all_results:
                logger.info(f"No images found for '{query}', using placeholders")
                return self._get_placeholder_images(query, num_images)

            return all_results[:num_images]
        except Exception as e:
            logger.error(f"Image search error for '{query}': {str(e)}")
            # Return local images if we have any, otherwise placeholders
            return local_images if local_images else self._get_placeholder_images(query, num_images)
    
    
    def _search_serpapi(self, query: str, num_images: int) -> List[Dict[str, str]]:
        """Search images using SerpAPI (Google Images)"""
        try:
            from serpapi import GoogleSearch
            
            params = {
                "q": query,
                "tbm": "isch",  # Image search
                "api_key": self.serpapi_key,
                "num": num_images,
                "safe": "active"  # Safe search
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            images = []
            if "images_results" in results:
                for img in results["images_results"][:num_images]:
                    images.append({
                        "url": img.get("original", img.get("thumbnail")),
                        "title": img.get("title", query),
                        "source": img.get("source", "Google Images"),
                        "thumbnail": img.get("thumbnail", "")
                    })
            
            logger.info(f"SerpAPI found {len(images)} images for '{query}'")
            return images
            
        except ImportError:
            logger.warning("SerpAPI library not installed. Install: pip install google-search-results")
            return self._search_duckduckgo(query, num_images)
        except Exception as e:
            logger.error(f"SerpAPI error: {str(e)}")
            return self._search_duckduckgo(query, num_images)
    
    
    def _search_duckduckgo(self, query: str, num_images: int) -> List[Dict[str, str]]:
        """Search images using DuckDuckGo (free, no API key)"""
        try:
            # DuckDuckGo instant answer API
            url = "https://duckduckgo.com/"
            params = {
                "q": query,
                "iax": "images",
                "ia": "images"
            }
            
            # First, get the vqd token
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            session = requests.Session()
            response = session.get(url, params={"q": query}, headers=headers, timeout=self.timeout)
            
            # Extract vqd token from response
            vqd = None
            for line in response.text.split('\n'):
                if 'vqd=' in line:
                    vqd = line.split('vqd=')[1].split('&')[0].strip('"').strip("'")
                    break
            
            if not vqd:
                logger.warning(f"Could not extract vqd token for query: {query}")
                return self._search_duckduckgo_fallback(query, num_images)
            
            # Now get the actual images
            image_url = "https://duckduckgo.com/i.js"
            params = {
                "l": "us-en",
                "o": "json",
                "q": query,
                "vqd": vqd,
                "f": ",,,",
                "p": "1"
            }
            
            response = session.get(image_url, params=params, headers=headers, timeout=self.timeout)

            # Simple rate-limit detection — if DuckDuckGo blocks us, return empty so caller can fallback
            if response.status_code == 429:
                logger.warning(f"DuckDuckGo rate limited (429) for query: {query}")
                return []

            data = response.json()
            
            images = []
            if "results" in data:
                for img in data["results"][:num_images]:
                    images.append({
                        "url": img.get("image", ""),
                        "title": img.get("title", query),
                        "source": img.get("source", "DuckDuckGo"),
                        "thumbnail": img.get("thumbnail", "")
                    })
            
            logger.info(f"DuckDuckGo found {len(images)} images for '{query}'")
            return images
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {str(e)}")
            return self._search_duckduckgo_fallback(query, num_images)
    
    
    def _search_duckduckgo_fallback(self, query: str, num_images: int) -> List[Dict[str, str]]:
        """
        Fallback method using DuckDuckGo Instant Answer API
        Returns placeholder/generic images if search fails
        """
        try:
            # Use ddgs library (new package name)
            try:
                from ddgs import DDGS
                
                ddgs = DDGS()
                results = ddgs.images(
                    keywords=query,
                    max_results=num_images,
                    safesearch='on'
                )
                
                images = []
                for img in results:
                    images.append({
                        "url": img.get("image", ""),
                        "title": img.get("title", query),
                        "source": img.get("source", "DuckDuckGo"),
                        "thumbnail": img.get("thumbnail", "")
                    })
                
                logger.info(f"DuckDuckGo fallback found {len(images)} images for '{query}'")
                return images
                    
            except ImportError:
                logger.warning("ddgs library not installed. Install: pip install ddgs")
                # Return hardcoded fallback images for common products
                return self._get_placeholder_images(query, num_images)
                
        except Exception as e:
            logger.error(f"DuckDuckGo fallback error: {str(e)}")
            # Return hardcoded fallback images
            return self._get_placeholder_images(query, num_images)
    
    
    def _get_placeholder_images(self, query: str, num_images: int) -> List[Dict[str, str]]:
        """
        Return hardcoded placeholder images for common agricultural products
        This ensures the app always has some visual aids even without API access
        """
        # Placeholder image database (can be expanded)
        placeholders = {
            "urea": [
                {
                    "url": "https://5.imimg.com/data5/SELLER/Default/2023/7/323661562/VS/XK/EH/139972460/urea-fertilizer-500x500.jpg",
                    "title": "Urea 46-0-0 Fertilizer",
                    "source": "Agricultural Supply",
                    "thumbnail": "",
                    "trusted": True
                }
            ],
            "dap": [
                {
                    "url": "https://5.imimg.com/data5/SELLER/Default/2022/11/LY/RU/QN/9636813/dap-fertilizer-500x500.jpg",
                    "title": "DAP 18-46-0 Fertilizer",
                    "source": "Agricultural Supply",
                    "thumbnail": "",
                    "trusted": True
                }
            ],
            "pesticide": [
                {
                    "url": "https://5.imimg.com/data5/SELLER/Default/2023/3/291766090/DZ/QV/JP/1588059/chlorpyrifos-20-ec-500x500.jpg",
                    "title": "Pesticide Product",
                    "source": "Agricultural Supply",
                    "thumbnail": "",
                    "trusted": True
                }
            ],
            "fertilizer": [
                {
                    "url": "https://5.imimg.com/data5/SELLER/Default/2021/1/HE/TZ/JO/22148148/npk-fertilizer-500x500.jpg",
                    "title": "NPK Fertilizer",
                    "source": "Agricultural Supply",
                    "thumbnail": "",
                    "trusted": True
                }
            ]
        }
        
        # Try to match query with placeholder categories
        query_lower = query.lower()
        for category, images in placeholders.items():
            if category in query_lower:
                return images[:num_images]
        
        # Default to generic fertilizer image
        return placeholders.get("fertilizer", [])[:num_images]
    
    
    def validate_image_url(self, url: str) -> bool:
        """
        Validate if image URL is accessible and is actually an image
        
        Args:
            url: Image URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Quick HEAD request to check if URL is accessible
            response = requests.head(url, timeout=3, allow_redirects=True)
            
            if response.status_code != 200:
                return False
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"URL is not an image: {url} (Content-Type: {content_type})")
                return False
            
            # Check content length (avoid huge files)
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB max
                logger.warning(f"Image too large: {url} ({content_length} bytes)")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Image validation failed for {url}: {str(e)}")
            return False
    
    
    def filter_and_validate_images(self, images: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Filter and validate image URLs
        
        Args:
            images: List of image dictionaries
            
        Returns:
            Filtered list of valid images
        """
        valid_images = []
        
        for img in images:
            url = img.get("url", "")
            if not url:
                continue
            
            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                continue
            
            # If image is from local DB or marked trusted, accept without network validation
            if img.get("local", False) or img.get("trusted", False):
                valid_images.append(img)
            else:
                # Prefer HTTPS
                if url.startswith('http://'):
                    https_url = url.replace('http://', 'https://', 1)
                    if self.validate_image_url(https_url):
                        img["url"] = https_url
                        valid_images.append(img)
                    elif self.validate_image_url(url):
                        valid_images.append(img)
                else:
                    if self.validate_image_url(url):
                        valid_images.append(img)
            
            # Stop if we have enough valid images
            if len(valid_images) >= self.max_images:
                break
        
        logger.info(f"Validated {len(valid_images)} out of {len(images)} images")
        return valid_images
    
    
    # Specialized search methods for different agricultural categories
    
    def search_fertilizer_images(self, product_name: str, include_generic: bool = True) -> List[Dict[str, str]]:
        """
        Search for fertilizer product images (local DB first, then SerpAPI)
        
        Args:
            product_name: Name of fertilizer (e.g., "Urea", "DAP")
            include_generic: Include generic fertilizer images if specific not found
            
        Returns:
            List of image dictionaries
        """
        # Try local database with category filter
        logger.info(f"Searching fertilizer images for: {product_name}")
        local_images = images_db.search_images(product_name, category="fertilizer", limit=self.max_images)
        
        if local_images and len(local_images) >= 2:
            logger.info(f"Found {len(local_images)} fertilizer images in local DB")
            return local_images[:self.max_images]
        
        # Fallback to SerpAPI if not enough in local DB
        logger.info(f"Using SerpAPI for fertilizer: {product_name}")
        queries = [
            f"{product_name} fertilizer bag India",
            f"{product_name} fertilizer packet agricultural"
        ]
        
        all_images = list(local_images)  # Start with what we have from local DB
        for query in queries[:2]:
            if len(all_images) >= self.max_images:
                break
            images = self.search_images(query, num_images=self.images_per_query)
            all_images.extend(images)
        
        return self.filter_and_validate_images(all_images)
    
    
    def search_pesticide_images(self, product_name: str) -> List[Dict[str, str]]:
        """
        Search for pesticide product images (local DB first, then SerpAPI)
        
        Args:
            product_name: Name of pesticide
            
        Returns:
            List of image dictionaries
        """
        # Try local database with category filter
        logger.info(f"Searching pesticide images for: {product_name}")
        local_images = images_db.search_images(product_name, category="pesticide", limit=self.max_images)
        
        if local_images and len(local_images) >= 2:
            logger.info(f"Found {len(local_images)} pesticide images in local DB")
            return local_images[:self.max_images]
        
        # Fallback to SerpAPI if not enough in local DB
        logger.info(f"Using SerpAPI for pesticide: {product_name}")
        queries = [
            f"{product_name} pesticide bottle India",
            f"{product_name} insecticide packaging agricultural"
        ]
        
        all_images = list(local_images)  # Start with what we have from local DB
        for query in queries[:2]:
            if len(all_images) >= self.max_images:
                break
            images = self.search_images(query, num_images=self.images_per_query)
            all_images.extend(images)
        
        return self.filter_and_validate_images(all_images)
    
    
    def search_crop_disease_images(self, disease_name: str, crop_name: str = "") -> List[Dict[str, str]]:
        """
        Search for crop disease symptom images
        
        Args:
            disease_name: Name of disease
            crop_name: Name of crop (optional)
            
        Returns:
            List of image dictionaries
        """
        queries = []
        
        if crop_name:
            queries.append(f"{crop_name} {disease_name} symptoms leaves")
            queries.append(f"{crop_name} {disease_name} affected plant")
        else:
            queries.append(f"{disease_name} crop disease symptoms")
            queries.append(f"{disease_name} plant infection")
        
        all_images = []
        for query in queries[:2]:
            images = self.search_images(query, num_images=self.images_per_query)
            all_images.extend(images)
            
            if len(all_images) >= self.max_images:
                break
        
        return self.filter_and_validate_images(all_images)
    
    
    def search_crop_images(self, crop_name: str, context: str = "seeds") -> List[Dict[str, str]]:
        """
        Search for crop-related images
        
        Args:
            crop_name: Name of crop
            context: Context for images (seeds, plant, harvest, etc.)
            
        Returns:
            List of image dictionaries
        """
        queries = [
            f"{crop_name} {context} India agricultural",
            f"{crop_name} variety {context}"
        ]
        
        all_images = []
        for query in queries[:2]:
            images = self.search_images(query, num_images=self.images_per_query)
            all_images.extend(images)
            
            if len(all_images) >= self.max_images:
                break
        
        return self.filter_and_validate_images(all_images)
    
    
    def search_equipment_images(self, equipment_type: str) -> List[Dict[str, str]]:
        """
        Search for agricultural equipment images
        
        Args:
            equipment_type: Type of equipment (sprayer, pump, etc.)
            
        Returns:
            List of image dictionaries
        """
        queries = [
            f"{equipment_type} agricultural India",
            f"{equipment_type} farming equipment"
        ]
        
        all_images = []
        for query in queries[:2]:
            images = self.search_images(query, num_images=self.images_per_query)
            all_images.extend(images)
            
            if len(all_images) >= self.max_images:
                break
        
        return self.filter_and_validate_images(all_images)
    
    
    def search_soil_images(self, context: str = "testing") -> List[Dict[str, str]]:
        """
        Search for soil-related images
        
        Args:
            context: Context for images (testing, types, health, etc.)
            
        Returns:
            List of image dictionaries
        """
        queries = [
            f"soil {context} kit India agricultural",
            f"soil {context} agriculture"
        ]
        
        all_images = []
        for query in queries[:2]:
            images = self.search_images(query, num_images=self.images_per_query)
            all_images.extend(images)
            
            if len(all_images) >= self.max_images:
                break
        
        return self.filter_and_validate_images(all_images)


# Singleton instance
image_search_service = ImageSearchService()


# Utility function for easy import
def search_agricultural_images(query: str, category: str = "general", **kwargs) -> List[Dict[str, str]]:
    """
    Convenience function to search agricultural images
    
    Args:
        query: Search query or product name
        category: Category of search (fertilizer, pesticide, crop_disease, crop, equipment, soil)
        **kwargs: Additional arguments for specific search methods
        
    Returns:
        List of image dictionaries
    """
    if category == "fertilizer":
        return image_search_service.search_fertilizer_images(query, **kwargs)
    elif category == "pesticide":
        return image_search_service.search_pesticide_images(query)
    elif category == "crop_disease":
        crop_name = kwargs.get("crop_name", "")
        return image_search_service.search_crop_disease_images(query, crop_name)
    elif category == "crop":
        context = kwargs.get("context", "seeds")
        return image_search_service.search_crop_images(query, context)
    elif category == "equipment":
        return image_search_service.search_equipment_images(query)
    elif category == "soil":
        context = kwargs.get("context", "testing")
        return image_search_service.search_soil_images(context)
    else:
        return image_search_service.search_images(query)


if __name__ == "__main__":
    # Test the image search service
    print("🧪 Testing Image Search Service\n")
    
    # Test fertilizer search
    print("1. Searching for Urea fertilizer images...")
    images = image_search_service.search_fertilizer_images("Urea")
    print(f"   Found {len(images)} images")
    for img in images:
        print(f"   - {img['title']}: {img['url'][:60]}...")
    
    print("\n2. Searching for pesticide images...")
    images = image_search_service.search_pesticide_images("Chlorpyrifos")
    print(f"   Found {len(images)} images")
    for img in images:
        print(f"   - {img['title']}: {img['url'][:60]}...")
    
    print("\n3. Searching for crop disease images...")
    images = image_search_service.search_crop_disease_images("rust", "wheat")
    print(f"   Found {len(images)} images")
    for img in images:
        print(f"   - {img['title']}: {img['url'][:60]}...")
    
    print("\n✅ Image Search Service test complete!")
