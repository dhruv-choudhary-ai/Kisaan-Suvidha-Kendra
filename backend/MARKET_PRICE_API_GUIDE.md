# Market Price API - Fallback Mechanism Documentation

## Overview

The market price service now implements a robust fallback mechanism to ensure farmers always get price information, even if the primary API fails. This guide explains the implementation, usage, and API details.

## Architecture

### Fallback Chain

```
User Request → get_commodity_prices()
                    ↓
            1. Try eNAM API
                    ↓
            (If fails or no data)
                    ↓
            2. Try data.gov.in Mandi API
                    ↓
            Return best available data
```

## API Sources

### 1. eNAM API (Primary)
- **Source**: National Agriculture Market (eNAM)
- **Endpoint**: `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070`
- **Coverage**: Major mandis integrated with eNAM
- **Update Frequency**: Daily
- **Advantages**: 
  - Official government data
  - High quality and verified
  - Comprehensive commodity coverage

### 2. data.gov.in Daily Mandi Prices (Fallback)
- **Source**: Ministry of Agriculture & Farmers Welfare
- **Endpoint**: `https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070`
- **Coverage**: Daily prices from various mandis across India
- **Update Frequency**: Daily
- **Advantages**:
  - Wider geographical coverage
  - More granular data
  - Multiple filter options

## Available Methods

### 1. `get_commodity_prices()` - Main Method with Fallback

```python
results = await agriculture_api_service.get_commodity_prices(
    commodity="Wheat",
    state="Punjab",
    district="Ludhiana"
)
```

**Parameters:**
- `commodity` (str): Commodity name (e.g., "Wheat", "Rice", "Tomato")
- `state` (str, optional): State name
- `district` (str, optional): District name

**Returns:**
- List of price records with normalized format

**Behavior:**
1. First tries eNAM API
2. If eNAM returns no data, automatically falls back to data.gov.in
3. Returns the first successful result
4. Logs which API was used

### 2. `get_daily_mandi_prices()` - Direct Access

```python
results = await agriculture_api_service.get_daily_mandi_prices(
    commodity="Wheat",
    state="Punjab",
    district="Ludhiana",
    market="Ludhiana",
    variety="Local",
    grade="FAQ"
)
```

**Parameters:**
- `commodity` (str, optional): Commodity name
- `state` (str, optional): State name
- `district` (str, optional): District name
- `market` (str, optional): Market/Mandi name
- `variety` (str, optional): Variety of commodity
- `grade` (str, optional): Grade of commodity

**Returns:**
- List of daily mandi price records

**Use Case:** When you need direct access to the mandi API with all filter options

## Data Format

### Normalized Response Structure

```python
{
    "state": "Punjab",
    "district": "Ludhiana",
    "market": "Ludhiana",
    "commodity": "Wheat",
    "variety": "Desi",
    "grade": "FAQ",
    "arrival_date": "2025-11-12",
    "min_price": 2000.00,
    "max_price": 2150.00,
    "modal_price": 2080.00,
    "price_date": "2025-11-12",
    "source": "data.gov.in"  # or "eNAM"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `state` | string | State where the market is located |
| `district` | string | District name |
| `market` | string | Market/Mandi name |
| `commodity` | string | Name of the commodity |
| `variety` | string | Variety/type of commodity |
| `grade` | string | Quality grade (FAQ, A, B, etc.) |
| `arrival_date` | string | Date when commodity arrived at mandi |
| `min_price` | float | Minimum price in ₹/quintal |
| `max_price` | float | Maximum price in ₹/quintal |
| `modal_price` | float | Most common/modal price in ₹/quintal |
| `price_date` | string | Date of price recording |
| `source` | string | Data source (eNAM or data.gov.in) |

## API Configuration

### Required Environment Variables

Add to your `.env` file:

```env
# Data.gov.in API Key
DATA_GOV_API_KEY=579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b

# Note: The above is a sample key with 10 records limit
# Get your own key from: https://data.gov.in
# Login → My Account → API Key
```

### Configuration in `config.py`

```python
class Config:
    # Agriculture API Configuration
    AGMARKNET_API_BASE = "https://api.data.gov.in/resource"
    DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY")
```

## Error Handling

### Logging

The service logs all API calls and errors:

```
✅ Successfully fetched 15 records from eNAM API
⚠️ eNAM API returned no data, trying data.gov.in fallback...
✅ Successfully fetched 12 records from data.gov.in fallback API
❌ Both APIs failed to return data
```

### HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Return data |
| 400 | Bad Request | Check parameters, log error |
| 403 | Forbidden | Check API key |
| 404 | Not Found | Try fallback |
| 500 | Server Error | Try fallback |

## Usage Examples

### Example 1: Basic Price Query

```python
import asyncio
from agriculture_apis import agriculture_api_service

async def get_wheat_prices():
    prices = await agriculture_api_service.get_commodity_prices(
        commodity="Wheat",
        state="Punjab"
    )
    
    if prices:
        for price in prices[:5]:
            print(f"{price['market']}: ₹{price['modal_price']}/quintal")
    else:
        print("No prices available")

asyncio.run(get_wheat_prices())
```

### Example 2: Specific Market Query

```python
async def get_specific_market():
    prices = await agriculture_api_service.get_daily_mandi_prices(
        commodity="Rice",
        state="Haryana",
        district="Karnal",
        market="Karnal"
    )
    
    if prices:
        avg_price = sum(p['modal_price'] for p in prices) / len(prices)
        print(f"Average rice price in Karnal: ₹{avg_price:.2f}/quintal")

asyncio.run(get_specific_market())
```

### Example 3: Price Comparison

```python
async def compare_markets():
    prices = await agriculture_api_service.get_commodity_prices(
        commodity="Tomato",
        state="Maharashtra"
    )
    
    if prices:
        markets = {}
        for p in prices:
            markets[p['market']] = p['modal_price']
        
        best_market = max(markets.items(), key=lambda x: x[1])
        print(f"Best price: {best_market[0]} - ₹{best_market[1]}/quintal")

asyncio.run(compare_markets())
```

## Testing

### Run the Test Suite

```bash
cd backend
python test_fallback_api.py
```

### Test Coverage

The test file (`test_fallback_api.py`) includes:

1. **Fallback Mechanism Test**: Verifies automatic fallback works
2. **Direct Mandi API Test**: Tests data.gov.in API independently
3. **eNAM API Test**: Tests eNAM API independently
4. **Data.gov.in API Test**: Tests fallback API independently

### Expected Output

```
✅ Success! Found 15 records
Sample data (first 2 records):
  Market: Ludhiana
  State: Punjab
  Commodity: Wheat
  Modal Price: ₹2080.0
  Source: eNAM
```

## Common Commodities

### Supported Commodities (Examples)

| English | Hindi | Common Varieties |
|---------|-------|------------------|
| Wheat | गेहूं | Desi, Hybrid, Sharbati |
| Rice | धान | Basmati, Non-Basmati, Parmal |
| Cotton | कपास | Desi, Hybrid, MCU-5 |
| Soybean | सोयाबीन | Yellow, Black |
| Tomato | टमाटर | Hybrid, Local |
| Onion | प्याज | Red, White |
| Potato | आलू | Red, White |
| Maize | मक्का | Hybrid, Desi |

## Integration with LangGraph Agents

The market price agent automatically uses this fallback mechanism:

```python
# From langgraph_kisaan_agents.py
market_data = run_async_safe(agriculture_api_service.get_commodity_prices(
    commodity=commodity,
    state=location.get("state"),
    district=location.get("district")
))
```

No changes needed to existing agent code - fallback is automatic!

## API Rate Limits

### Sample API Key
- **Limit**: 10 records per request
- **Rate**: No specified limit

### Production API Key (Recommended)
1. Visit: https://data.gov.in
2. Login/Register
3. Go to "My Account"
4. Generate API Key
5. Update `.env` with your key

### Benefits of Production Key
- Higher record limits (up to 100+)
- Better rate limits
- Priority support
- Access to more datasets

## Troubleshooting

### Issue: Both APIs return no data

**Possible Causes:**
1. Incorrect commodity name
2. No data available for specified location
3. API key issue
4. Network connectivity

**Solutions:**
```python
# Try with just commodity, no location
prices = await agriculture_api_service.get_commodity_prices(
    commodity="Wheat"
)

# Try different commodity spellings
for name in ["Wheat", "wheat", "WHEAT", "Gehun"]:
    prices = await agriculture_api_service.get_commodity_prices(commodity=name)
    if prices:
        break
```

### Issue: 403 Forbidden Error

**Solution:** Check your API key in `.env` file:
```env
DATA_GOV_API_KEY=your_actual_key_here
```

### Issue: Timeout Errors

**Solution:** Timeout is set to 10 seconds. Increase if needed:
```python
# In _get_enam_prices or _get_datagov_mandi_prices
timeout=aiohttp.ClientTimeout(total=15)  # Increase to 15 seconds
```

## Performance Optimization

### Caching (Future Enhancement)

Consider implementing Redis caching:
```python
# Pseudo-code for future implementation
@cache_with_ttl(minutes=30)
async def get_commodity_prices(...):
    # Existing code
```

### Batch Requests

For multiple commodities:
```python
async def get_multiple_commodities(commodities, state):
    tasks = [
        agriculture_api_service.get_commodity_prices(c, state)
        for c in commodities
    ]
    results = await asyncio.gather(*tasks)
    return dict(zip(commodities, results))
```

## Changelog

### Version 2.0 (Current)
- ✅ Added data.gov.in daily mandi API as fallback
- ✅ Implemented automatic fallback mechanism
- ✅ Added data normalization
- ✅ Enhanced error handling and logging
- ✅ Added comprehensive test suite
- ✅ Added `get_daily_mandi_prices()` method

### Version 1.0 (Previous)
- Basic eNAM API integration
- Simple error handling

## Support & Resources

### Official Documentation
- **data.gov.in API**: https://data.gov.in/help/api
- **eNAM Portal**: https://enam.gov.in
- **Agmarknet**: https://agmarknet.gov.in

### Contact
- **Mandi Helpline**: 1800-270-0224
- **data.gov.in Support**: support@data.gov.in

## License

This implementation follows the **Government Open Data License - India** for the use of data.gov.in APIs.

---

**Last Updated**: November 12, 2025
**Author**: Kisaan Suvidha Kendra Development Team
