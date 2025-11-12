"""
Test script to verify the market price API fallback mechanism
Tests both eNAM and data.gov.in mandi price APIs
"""

import asyncio
import logging
from agriculture_apis import agriculture_api_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_commodity_prices_with_fallback():
    """Test the main get_commodity_prices method with fallback"""
    print("\n" + "="*80)
    print("TEST 1: Testing get_commodity_prices with fallback mechanism")
    print("="*80 + "\n")
    
    test_cases = [
        {"commodity": "Wheat", "state": "Punjab", "district": None},
        {"commodity": "Rice", "state": "Haryana", "district": None},
        {"commodity": "Tomato", "state": "Maharashtra", "district": None},
        {"commodity": "Onion", "state": None, "district": None},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Commodity: {test_case['commodity']}")
        print(f"State: {test_case['state'] or 'Not specified'}")
        print(f"District: {test_case['district'] or 'Not specified'}")
        
        try:
            results = await agriculture_api_service.get_commodity_prices(
                commodity=test_case['commodity'],
                state=test_case['state'],
                district=test_case['district']
            )
            
            if results:
                print(f"✅ Success! Found {len(results)} records")
                print("\nSample data (first 2 records):")
                for record in results[:2]:
                    print(f"\n  Market: {record.get('market', 'N/A')}")
                    print(f"  State: {record.get('state', 'N/A')}")
                    print(f"  District: {record.get('district', 'N/A')}")
                    print(f"  Commodity: {record.get('commodity', 'N/A')}")
                    print(f"  Variety: {record.get('variety', 'N/A')}")
                    print(f"  Modal Price: ₹{record.get('modal_price', 0)}")
                    print(f"  Min Price: ₹{record.get('min_price', 0)}")
                    print(f"  Max Price: ₹{record.get('max_price', 0)}")
                    print(f"  Source: {record.get('source', 'eNAM')}")
            else:
                print("❌ No data returned from either API")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # Add delay between requests
        await asyncio.sleep(1)

async def test_direct_mandi_api():
    """Test direct access to data.gov.in mandi API"""
    print("\n" + "="*80)
    print("TEST 2: Testing direct data.gov.in daily mandi prices API")
    print("="*80 + "\n")
    
    test_cases = [
        {
            "commodity": "Wheat",
            "state": "Punjab",
            "description": "Wheat prices in Punjab"
        },
        {
            "commodity": "Rice",
            "state": "West Bengal",
            "description": "Rice prices in West Bengal"
        },
        {
            "commodity": None,
            "state": "Karnataka",
            "description": "All commodities in Karnataka"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['description']} ---")
        
        try:
            results = await agriculture_api_service.get_daily_mandi_prices(
                commodity=test_case['commodity'],
                state=test_case['state']
            )
            
            if results:
                print(f"✅ Success! Found {len(results)} records")
                
                # Show unique commodities
                commodities = set(r.get('commodity', '') for r in results)
                print(f"\nCommodities found: {', '.join(sorted(commodities))}")
                
                # Show price range
                prices = [r.get('modal_price', 0) for r in results if r.get('modal_price', 0) > 0]
                if prices:
                    print(f"Price range: ₹{min(prices):.2f} - ₹{max(prices):.2f}")
                
                # Show sample record
                if results:
                    print(f"\nSample record:")
                    sample = results[0]
                    for key, value in sample.items():
                        print(f"  {key}: {value}")
            else:
                print("❌ No data returned")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        await asyncio.sleep(1)

async def test_enam_api_directly():
    """Test eNAM API directly"""
    print("\n" + "="*80)
    print("TEST 3: Testing eNAM API directly")
    print("="*80 + "\n")
    
    try:
        results = await agriculture_api_service._get_enam_prices(
            commodity="Wheat",
            state="Punjab"
        )
        
        if results:
            print(f"✅ eNAM API Success! Found {len(results)} records")
            if results:
                print("\nFirst record:")
                for key, value in results[0].items():
                    print(f"  {key}: {value}")
        else:
            print("⚠️ eNAM API returned no data (this will trigger fallback)")
    
    except Exception as e:
        print(f"❌ eNAM API Error: {str(e)}")

async def test_datagov_api_directly():
    """Test data.gov.in mandi API directly"""
    print("\n" + "="*80)
    print("TEST 4: Testing data.gov.in mandi API directly")
    print("="*80 + "\n")
    
    try:
        results = await agriculture_api_service._get_datagov_mandi_prices(
            commodity="Wheat",
            state="Punjab"
        )
        
        if results:
            print(f"✅ Data.gov.in API Success! Found {len(results)} records")
            if results:
                print("\nFirst record:")
                for key, value in results[0].items():
                    print(f"  {key}: {value}")
        else:
            print("⚠️ Data.gov.in API returned no data")
    
    except Exception as e:
        print(f"❌ Data.gov.in API Error: {str(e)}")

async def main():
    """Run all tests"""
    print("\n🧪 STARTING MARKET PRICE API FALLBACK TESTS")
    print("=" * 80)
    
    # Test 1: Main method with fallback
    await test_commodity_prices_with_fallback()
    
    # Test 2: Direct mandi API
    await test_direct_mandi_api()
    
    # Test 3: eNAM API directly
    await test_enam_api_directly()
    
    # Test 4: Data.gov.in API directly
    await test_datagov_api_directly()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
