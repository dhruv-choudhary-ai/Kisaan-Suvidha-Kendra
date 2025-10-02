"""
Initialize SQLite database for Kisaan Voice Assistant
Run this script to create the SQLite database with all necessary tables
"""
import sqlite3
import os
from datetime import datetime

def init_sqlite_database(db_path='kisaan_assist.db'):
    """Initialize SQLite database with required schema"""
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)
    
    print(f"Creating new SQLite database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create farmers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone_number TEXT UNIQUE NOT NULL,
            village TEXT,
            district TEXT,
            state TEXT,
            land_size_acres REAL,
            soil_type TEXT,
            irrigation_type TEXT,
            primary_crops TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create voice_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voice_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            farmer_id INTEGER,
            language TEXT DEFAULT 'hindi',
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            total_queries INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (farmer_id) REFERENCES farmers(id)
        )
    """)
    
    # Create conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            farmer_id INTEGER,
            user_message TEXT,
            bot_response TEXT,
            query_type TEXT,
            language TEXT DEFAULT 'hindi',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES voice_sessions(session_id),
            FOREIGN KEY (farmer_id) REFERENCES farmers(id)
        )
    """)
    
    # Create crop_information table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crop_information (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name TEXT NOT NULL,
            crop_name_hindi TEXT,
            crop_type TEXT,
            growing_season TEXT,
            soil_requirement TEXT,
            water_requirement TEXT,
            pest_diseases TEXT,
            market_demand TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create government_schemes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS government_schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_name TEXT NOT NULL,
            scheme_name_hindi TEXT,
            description TEXT,
            description_hindi TEXT,
            eligibility TEXT,
            how_to_apply TEXT,
            state TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create farmer_queries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmer_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER,
            session_id TEXT,
            query_text TEXT NOT NULL,
            query_type TEXT,
            response_text TEXT,
            language TEXT DEFAULT 'hindi',
            resolved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_id) REFERENCES farmers(id),
            FOREIGN KEY (session_id) REFERENCES voice_sessions(session_id)
        )
    """)
    
    # Insert sample crop data
    sample_crops = [
        ('Wheat', 'गेहूं', 'Cereal', 'Rabi', 'Loamy soil', 'Medium', 'Rust, Aphids', 'High'),
        ('Rice', 'चावल', 'Cereal', 'Kharif', 'Clay soil', 'High', 'Blast, Brown planthopper', 'High'),
        ('Cotton', 'कपास', 'Cash Crop', 'Kharif', 'Black soil', 'Medium', 'Bollworm, Aphids', 'High'),
        ('Sugarcane', 'गन्ना', 'Cash Crop', 'Year-round', 'Loamy soil', 'High', 'Red rot, Whitefly', 'High'),
        ('Soybean', 'सोयाबीन', 'Oilseed', 'Kharif', 'Well-drained soil', 'Medium', 'Pod borer, Yellow mosaic', 'Medium')
    ]
    
    cursor.executemany("""
        INSERT INTO crop_information 
        (crop_name, crop_name_hindi, crop_type, growing_season, soil_requirement, water_requirement, pest_diseases, market_demand)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_crops)
    
    # Insert sample government schemes
    sample_schemes = [
        ('PM-KISAN', 'पीएम-किसान', 
         'Income support to farmers', 
         'किसानों को आय सहायता',
         'All landholding farmers',
         'Register on PM-KISAN portal',
         None, 1),
        ('Kisan Credit Card', 'किसान क्रेडिट कार्ड',
         'Credit facility for farmers',
         'किसानों के लिए ऋण सुविधा',
         'Farmers with land',
         'Apply through banks',
         None, 1),
        ('Fasal Bima Yojana', 'फसल बीमा योजना',
         'Crop insurance scheme',
         'फसल बीमा योजना',
         'All farmers',
         'Enroll during crop season',
         None, 1)
    ]
    
    cursor.executemany("""
        INSERT INTO government_schemes
        (scheme_name, scheme_name_hindi, description, description_hindi, eligibility, how_to_apply, state, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_schemes)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_farmers_phone ON farmers(phone_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_id ON voice_sessions(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_farmer ON farmer_queries(farmer_id)")
    
    conn.commit()
    conn.close()
    
    print(f"✅ SQLite database initialized successfully!")
    print(f"📊 Created tables: farmers, voice_sessions, conversations, crop_information, government_schemes, farmer_queries")
    print(f"📁 Database file: {os.path.abspath(db_path)}")
    
    return True

if __name__ == "__main__":
    init_sqlite_database()
