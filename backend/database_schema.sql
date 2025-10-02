-- Kisaan Voice Assistant Database Schema
-- PostgreSQL Database: kisaan_assist

-- Drop existing tables if they exist
DROP TABLE IF EXISTS crop_advisories CASCADE;
DROP TABLE IF EXISTS pest_disease_reports CASCADE;
DROP TABLE IF EXISTS crops CASCADE;
DROP TABLE IF EXISTS farmers CASCADE;
DROP TABLE IF EXISTS government_schemes CASCADE;
DROP TABLE IF EXISTS weather_cache CASCADE;
DROP TABLE IF EXISTS market_prices_cache CASCADE;

-- Farmers Table
CREATE TABLE farmers (
    farmer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    village VARCHAR(255) NOT NULL,
    district VARCHAR(255) NOT NULL,
    state VARCHAR(255) NOT NULL,
    land_size_acres DECIMAL(10, 2),
    soil_type VARCHAR(100),
    irrigation_type VARCHAR(100),
    primary_crops TEXT[],
    registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crops Table
CREATE TABLE crops (
    crop_id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(farmer_id) ON DELETE CASCADE,
    crop_name VARCHAR(255) NOT NULL,
    crop_variety VARCHAR(255),
    sowing_date DATE NOT NULL,
    expected_harvest_date DATE,
    land_area_acres DECIMAL(10, 2),
    current_stage VARCHAR(100), -- germination, vegetative, flowering, harvest
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crop Advisories Table
CREATE TABLE crop_advisories (
    advisory_id SERIAL PRIMARY KEY,
    crop_id INTEGER REFERENCES crops(crop_id) ON DELETE CASCADE,
    advisory_date DATE NOT NULL,
    advisory_type VARCHAR(100) NOT NULL, -- pest_control, fertilizer, irrigation, disease
    description TEXT NOT NULL,
    severity VARCHAR(50), -- low, medium, high, critical
    action_required TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pest and Disease Reports Table
CREATE TABLE pest_disease_reports (
    report_id SERIAL PRIMARY KEY,
    farmer_id INTEGER REFERENCES farmers(farmer_id) ON DELETE CASCADE,
    crop_id INTEGER REFERENCES crops(crop_id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    symptoms TEXT NOT NULL,
    image_url TEXT,
    identified_issue VARCHAR(255),
    recommended_treatment TEXT,
    severity VARCHAR(50),
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, resolved
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Government Schemes Table
CREATE TABLE government_schemes (
    scheme_id SERIAL PRIMARY KEY,
    scheme_name VARCHAR(500) NOT NULL,
    scheme_name_hindi VARCHAR(500),
    description TEXT NOT NULL,
    description_hindi TEXT,
    eligibility TEXT,
    how_to_apply TEXT,
    state VARCHAR(255), -- NULL means applicable to all states
    district VARCHAR(255), -- NULL means applicable to all districts
    scheme_url TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather Cache Table (to reduce API calls)
CREATE TABLE weather_cache (
    cache_id SERIAL PRIMARY KEY,
    location VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    temperature DECIMAL(5, 2),
    humidity INTEGER,
    rainfall DECIMAL(10, 2),
    wind_speed DECIMAL(5, 2),
    weather_condition VARCHAR(255),
    forecast_data JSONB,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP,
    UNIQUE(location, latitude, longitude)
);

-- Market Prices Cache Table
CREATE TABLE market_prices_cache (
    price_id SERIAL PRIMARY KEY,
    commodity VARCHAR(255) NOT NULL,
    market_name VARCHAR(255),
    state VARCHAR(255),
    district VARCHAR(255),
    min_price DECIMAL(10, 2),
    max_price DECIMAL(10, 2),
    modal_price DECIMAL(10, 2),
    price_date DATE NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100) -- agmarknet, data.gov.in, etc
);

-- Create indexes for better query performance
CREATE INDEX idx_farmers_phone ON farmers(phone_number);
CREATE INDEX idx_farmers_district_state ON farmers(district, state);
CREATE INDEX idx_crops_farmer_id ON crops(farmer_id);
CREATE INDEX idx_crops_sowing_date ON crops(sowing_date);
CREATE INDEX idx_advisories_crop_id ON crop_advisories(crop_id);
CREATE INDEX idx_advisories_date ON crop_advisories(advisory_date);
CREATE INDEX idx_pest_reports_farmer_id ON pest_disease_reports(farmer_id);
CREATE INDEX idx_pest_reports_status ON pest_disease_reports(status);
CREATE INDEX idx_schemes_state ON government_schemes(state);
CREATE INDEX idx_schemes_active ON government_schemes(active);
CREATE INDEX idx_weather_location ON weather_cache(location);
CREATE INDEX idx_market_commodity ON market_prices_cache(commodity);
CREATE INDEX idx_market_date ON market_prices_cache(price_date);

-- Insert sample government schemes data
INSERT INTO government_schemes (scheme_name, scheme_name_hindi, description, description_hindi, eligibility, how_to_apply, state) VALUES
('PM-KISAN', 'प्रधानमंत्री किसान सम्मान निधि', 
 'Financial assistance of Rs. 6000 per year to all farmer families', 
 'सभी किसान परिवारों को प्रति वर्ष 6000 रुपये की वित्तीय सहायता',
 'All landholding farmers', 
 'Visit PM-KISAN portal or contact local agriculture office',
 NULL),

('Kisan Credit Card', 'किसान क्रेडिट कार्ड', 
 'Credit facility for farmers to meet short-term agricultural needs',
 'किसानों को अल्पकालिक कृषि आवश्यकताओं के लिए ऋण सुविधा',
 'All farmers with land holding',
 'Apply through banks or cooperative societies',
 NULL),

('Pradhan Mantri Fasal Bima Yojana', 'प्रधानमंत्री फसल बीमा योजना',
 'Crop insurance scheme providing financial support in case of crop failure',
 'फसल विफलता की स्थिति में वित्तीय सहायता प्रदान करने वाली फसल बीमा योजना',
 'All farmers growing notified crops',
 'Apply through banks, CSCs, or agriculture offices',
 NULL),

('Soil Health Card Scheme', 'मृदा स्वास्थ्य कार्ड योजना',
 'Free soil testing and recommendations for balanced fertilizer use',
 'संतुलित उर्वरक उपयोग के लिए मुफ्त मिट्टी परीक्षण और सिफारिशें',
 'All farmers',
 'Contact district agriculture office or soil testing lab',
 NULL),

('Kisan Call Center', 'किसान कॉल सेंटर',
 '24x7 toll-free helpline for farming related queries',
 'कृषि संबंधी प्रश्नों के लिए 24x7 टोल-फ्री हेल्पलाइन',
 'All farmers',
 'Call 1800-180-1551',
 NULL);

-- Create stored procedures for common operations

-- Procedure to get farmer's crop information
CREATE OR REPLACE FUNCTION sp_get_farmer_crops(p_farmer_id INTEGER)
RETURNS TABLE (
    crop_id INTEGER,
    crop_name VARCHAR,
    crop_variety VARCHAR,
    sowing_date DATE,
    expected_harvest_date DATE,
    current_stage VARCHAR
) AS $
BEGIN
    RETURN QUERY
    SELECT c.crop_id, c.crop_name, c.crop_variety, c.sowing_date, 
           c.expected_harvest_date, c.current_stage
    FROM crops c
    WHERE c.farmer_id = p_farmer_id
    ORDER BY c.sowing_date DESC;
END;
$ LANGUAGE plpgsql;

-- Procedure to get active advisories for a crop
CREATE OR REPLACE FUNCTION sp_get_crop_advisories(p_crop_id INTEGER)
RETURNS TABLE (
    advisory_id INTEGER,
    advisory_date DATE,
    advisory_type VARCHAR,
    description TEXT,
    severity VARCHAR
) AS $
BEGIN
    RETURN QUERY
    SELECT ca.advisory_id, ca.advisory_date, ca.advisory_type, 
           ca.description, ca.severity
    FROM crop_advisories ca
    WHERE ca.crop_id = p_crop_id
    ORDER BY ca.advisory_date DESC
    LIMIT 10;
END;
$ LANGUAGE plpgsql;

-- Procedure to log pest disease report
CREATE OR REPLACE FUNCTION sp_create_pest_report(
    p_farmer_id INTEGER,
    p_crop_id INTEGER,
    p_symptoms TEXT,
    p_severity VARCHAR
)
RETURNS INTEGER AS $
DECLARE
    v_report_id INTEGER;
BEGIN
    INSERT INTO pest_disease_reports (farmer_id, crop_id, report_date, symptoms, severity, status)
    VALUES (p_farmer_id, p_crop_id, CURRENT_DATE, p_symptoms, p_severity, 'open')
    RETURNING report_id INTO v_report_id;
    
    RETURN v_report_id;
END;
$ LANGUAGE plpgsql;

-- Procedure to get government schemes by state
CREATE OR REPLACE FUNCTION sp_get_schemes_by_state(p_state VARCHAR DEFAULT NULL)
RETURNS TABLE (
    scheme_id INTEGER,
    scheme_name VARCHAR,
    scheme_name_hindi VARCHAR,
    description TEXT,
    description_hindi TEXT,
    eligibility TEXT,
    how_to_apply TEXT
) AS $
BEGIN
    RETURN QUERY
    SELECT gs.scheme_id, gs.scheme_name, gs.scheme_name_hindi,
           gs.description, gs.description_hindi, gs.eligibility, gs.how_to_apply
    FROM government_schemes gs
    WHERE gs.active = TRUE
      AND (gs.state IS NULL OR gs.state = p_state)
    ORDER BY gs.scheme_name;
END;
$ LANGUAGE plpgsql;

-- Trigger to update last_updated timestamp on farmers table
CREATE OR REPLACE FUNCTION update_farmer_timestamp()
RETURNS TRIGGER AS $
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_farmer_timestamp
BEFORE UPDATE ON farmers
FOR EACH ROW
EXECUTE FUNCTION update_farmer_timestamp();

-- Trigger to update updated_at timestamp on crops table
CREATE OR REPLACE FUNCTION update_crop_timestamp()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_crop_timestamp
BEFORE UPDATE ON crops
FOR EACH ROW
EXECUTE FUNCTION update_crop_timestamp();

-- Insert sample data for testing
INSERT INTO farmers (name, phone_number, village, district, state, land_size_acres, soil_type, irrigation_type, primary_crops) VALUES
('राजेश कुमार', '9876543210', 'खेड़ली', 'इंदौर', 'मध्य प्रदेश', 5.5, 'काली मिट्टी', 'नहर', ARRAY['गेहूं', 'सोयाबीन']),
('सुरेश पटेल', '9876543211', 'पिपल्या', 'देवास', 'मध्य प्रदेश', 3.2, 'लाल मिट्टी', 'बोरवेल', ARRAY['धान', 'मक्का']),
('रमेश शर्मा', '9876543212', 'खंडवा रोड', 'खंडवा', 'मध्य प्रदेश', 7.8, 'काली मिट्टी', 'नहर', ARRAY['कपास', 'गेहूं']);

COMMIT;