"""
Local Image Database for Agricultural Products
Stores product names and their image URLs for fast retrieval
Falls back to SerpAPI only when images not found locally
"""

import sqlite3
import os
import logging
from typing import List, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ImagesDatabase:
    """Local database for storing and retrieving product images"""
    
    def __init__(self, db_path: str = "images.db"):
        self.db_path = db_path
        self._init_db()
        self._populate_initial_data()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    keywords TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Images table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    source TEXT,
                    is_primary BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_products_name 
                ON products(name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_products_category 
                ON products(category)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_images_product 
                ON images(product_id)
            """)
            
            logger.info("Image database initialized")
    
    def _populate_initial_data(self):
        """Populate database with common agricultural products"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if already populated
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] > 0:
                return
            
            logger.info("Populating initial image data...")
            
            # Fertilizers
            fertilizers = [
                {
                    "name": "Urea",
                    "keywords": "urea,46-0-0,nitrogen fertilizer,यूरिया",
                    "images": [
                        {
                            "url": "https://www.spic.in/wp-content/uploads/2021/10/01.-BHARAT-UREA.png",
                            "title": "Bharat Urea (SPIC Neem Coated)",
                            "source": "SPIC"
                        },
                        {
                            "url": "https://5.imimg.com/data5/SELLER/Default/2023/7/323661562/VS/XK/EH/139972460/urea-fertilizer-500x500.jpg",
                            "title": "Urea 46-0-0 Fertilizer Bag",
                            "source": "IndiaMART"
                        }
                    ]
                },
                {
                    "name": "DAP",
                    "keywords": "dap,18-46-0,diammonium phosphate,डीएपी",
                    "images": [
                        {
                            "url": "https://5.imimg.com/data5/SELLER/Default/2022/11/LY/RU/QN/9636813/dap-fertilizer-500x500.jpg",
                            "title": "DAP 18-46-0 Fertilizer",
                            "source": "IndiaMART"
                        },
                        {
                            "url": "https://www.iffcobazar.in/images/products/DAP.jpg",
                            "title": "IFFCO DAP Fertilizer",
                            "source": "IFFCO"
                        }
                    ]
                },
                {
                    "name": "MOP",
                    "keywords": "mop,potash,0-0-60,muriate of potash,पोटाश",
                    "images": [
                        {
                            "url": "https://5.imimg.com/data5/SELLER/Default/2021/9/RC/WP/DQ/12345678/muriate-of-potash-500x500.jpg",
                            "title": "MOP Muriate of Potash",
                            "source": "IndiaMART"
                        }
                    ]
                },
                {
                    "name": "NPK",
                    "keywords": "npk,complex fertilizer,एनपीके",
                    "images": [
                        {
                            "url": "https://5.imimg.com/data5/SELLER/Default/2021/1/HE/TZ/JO/22148148/npk-fertilizer-500x500.jpg",
                            "title": "NPK Complex Fertilizer",
                            "source": "IndiaMART"
                        }
                    ]
                },
                {
                    "name": "SSP",
                    "keywords": "ssp,single super phosphate,सुपर फॉस्फेट",
                    "images": [
                        {
                            "url": "https://5.imimg.com/data5/SELLER/Default/2020/11/HX/JV/FN/12345678/ssp-fertilizer-500x500.jpg",
                            "title": "SSP Single Super Phosphate",
                            "source": "IndiaMART"
                        }
                    ]
                }
            ]
            
            # Pesticides
            pesticides = [
                {
                    "name": "Chlorpyrifos",
                    "keywords": "chlorpyrifos,क्लोरपायरीफॉस,insecticide",
                    "images": [
                        {
                            "url": "https://5.imimg.com/data5/SELLER/Default/2023/3/291766090/DZ/QV/JP/1588059/chlorpyrifos-20-ec-500x500.jpg",
                            "title": "Chlorpyrifos 20% EC",
                            "source": "IndiaMART"
                        },
                        {
                            "url": "https://agrivruddhi.com/cdn/shop/files/Predator_-AV.png",
                            "title": "Predator Chlorpyrifos Insecticide",
                            "source": "Agrivruddhi"
                        }
                    ]
                },
                {
                    "name": "Imidacloprid",
                    "keywords": "imidacloprid,इमिडाक्लोप्रिड,insecticide",
                    "images": [
                        {
                            "url": "https://5.imimg.com/data5/SELLER/Default/2021/5/AB/CD/EF/imidacloprid-500x500.jpg",
                            "title": "Imidacloprid 17.8% SL",
                            "source": "IndiaMART"
                        }
                    ]
                },
                {
                    "name": "Cypermethrin",
                    "keywords": "cypermethrin,साइपरमेथ्रिन,insecticide",
                    "images": [
                        {
                            "url": "https://5.imimg.com/data5/SELLER/Default/2022/8/cypermethrin-500x500.jpg",
                            "title": "Cypermethrin 10% EC",
                            "source": "IndiaMART"
                        }
                    ]
                },
                {
                    "name": "Neem Oil",
                    "keywords": "neem,neem oil,organic pesticide,नीम तेल",
                    "images": [
                        {
                            "url": "https://5.imimg.com/data5/SELLER/Default/2023/1/neem-oil-pesticide-500x500.jpg",
                            "title": "Neem Oil Organic Pesticide",
                            "source": "IndiaMART"
                        }
                    ]
                }
            ]
            
            # Insert fertilizers
            for fert in fertilizers:
                cursor.execute(
                    "INSERT INTO products (name, category, keywords) VALUES (?, ?, ?)",
                    (fert["name"], "fertilizer", fert["keywords"])
                )
                product_id = cursor.lastrowid
                
                for idx, img in enumerate(fert["images"]):
                    cursor.execute(
                        "INSERT INTO images (product_id, url, title, source, is_primary) VALUES (?, ?, ?, ?, ?)",
                        (product_id, img["url"], img["title"], img["source"], 1 if idx == 0 else 0)
                    )
            
            # Insert pesticides
            for pest in pesticides:
                cursor.execute(
                    "INSERT INTO products (name, category, keywords) VALUES (?, ?, ?)",
                    (pest["name"], "pesticide", pest["keywords"])
                )
                product_id = cursor.lastrowid
                
                for idx, img in enumerate(pest["images"]):
                    cursor.execute(
                        "INSERT INTO images (product_id, url, title, source, is_primary) VALUES (?, ?, ?, ?, ?)",
                        (product_id, img["url"], img["title"], img["source"], 1 if idx == 0 else 0)
                    )
            
            logger.info(f"Inserted {len(fertilizers)} fertilizers and {len(pesticides)} pesticides")
    
    def search_images(self, query: str, category: Optional[str] = None, limit: int = 4) -> List[Dict[str, str]]:
        """
        Search for images in local database
        
        Args:
            query: Search query (product name or keyword)
            category: Optional category filter (fertilizer, pesticide, crop, disease)
            limit: Maximum number of images to return
            
        Returns:
            List of image dictionaries with url, title, source
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query_lower = query.lower()
            
            # Build SQL query
            sql = """
                SELECT DISTINCT i.url, i.title, i.source, i.is_primary, p.name as product_name
                FROM images i
                JOIN products p ON i.product_id = p.id
                WHERE (
                    LOWER(p.name) LIKE ? OR
                    LOWER(p.keywords) LIKE ?
                )
            """
            params = [f"%{query_lower}%", f"%{query_lower}%"]
            
            if category:
                sql += " AND p.category = ?"
                params.append(category)
            
            sql += " ORDER BY i.is_primary DESC, i.id LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            images = []
            for row in rows:
                images.append({
                    "url": row["url"],
                    "title": row["title"] or row["product_name"],
                    "source": row["source"] or "Local DB",
                    "thumbnail": "",
                    "local": True  # Mark as from local DB
                })
            
            logger.info(f"Found {len(images)} images in local DB for query: {query}")
            return images
    
    def add_product(self, name: str, category: str, keywords: str, images: List[Dict[str, str]]):
        """Add a new product with images to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert product
            cursor.execute(
                "INSERT INTO products (name, category, keywords) VALUES (?, ?, ?)",
                (name, category, keywords)
            )
            product_id = cursor.lastrowid
            
            # Insert images
            for idx, img in enumerate(images):
                cursor.execute(
                    "INSERT INTO images (product_id, url, title, source, is_primary) VALUES (?, ?, ?, ?, ?)",
                    (product_id, img["url"], img.get("title", name), img.get("source", "Manual"), 1 if idx == 0 else 0)
                )
            
            logger.info(f"Added product '{name}' with {len(images)} images")
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM images")
            total_images = cursor.fetchone()[0]
            
            cursor.execute("SELECT category, COUNT(*) FROM products GROUP BY category")
            by_category = {row[0]: row[1] for row in cursor.fetchall()}
            
            return {
                "total_products": total_products,
                "total_images": total_images,
                "by_category": by_category
            }


# Singleton instance
images_db = ImagesDatabase()


if __name__ == "__main__":
    # Test the database
    print("🗄️ Testing Image Database\n")
    
    stats = images_db.get_stats()
    print(f"Database Stats:")
    print(f"  Total Products: {stats['total_products']}")
    print(f"  Total Images: {stats['total_images']}")
    print(f"  By Category: {stats['by_category']}\n")
    
    # Test searches
    print("Test 1: Search 'Urea'")
    results = images_db.search_images("Urea")
    print(f"  Found {len(results)} images")
    for img in results:
        print(f"    - {img['title']}: {img['url'][:60]}...")
    
    print("\nTest 2: Search 'Chlorpyrifos' in pesticides")
    results = images_db.search_images("Chlorpyrifos", category="pesticide")
    print(f"  Found {len(results)} images")
    for img in results:
        print(f"    - {img['title']}: {img['url'][:60]}...")
    
    print("\nTest 3: Search with Hindi keyword 'यूरिया'")
    results = images_db.search_images("यूरिया")
    print(f"  Found {len(results)} images")
    for img in results:
        print(f"    - {img['title']}")
    
    print("\n✅ Database test complete!")
