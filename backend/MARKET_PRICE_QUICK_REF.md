# Market Price API - Quick Reference

## 🚀 Quick Start

```python
from agriculture_apis import agriculture_api_service

# Simple query
prices = await agriculture_api_service.get_commodity_prices(
    commodity="Wheat",
    state="Punjab"
)

# Advanced query with all filters
prices = await agriculture_api_service.get_daily_mandi_prices(
    commodity="Rice",
    state="West Bengal",
    district="Coochbehar",
    market="Toofanganj",
    variety="Fine",
    grade="FAQ"
)
```

## 🔄 How Fallback Works

```
Request → eNAM API (Primary)
              ↓
         Has Data? Yes → Return Data ✅
              ↓ No
    data.gov.in Mandi API (Fallback)
              ↓
         Has Data? Yes → Return Data ✅
              ↓ No
          Return [] ❌
```

## 📊 Data Format

```python
{
    "commodity": "Rice",
    "state": "West Bengal",
    "district": "Coochbehar",
    "market": "Toofanganj",
    "variety": "Fine",
    "grade": "FAQ",
    "modal_price": 4000.0,      # Main price
    "min_price": 3900.0,
    "max_price": 4100.0,
    "arrival_date": "06/11/2025",
    "source": "data.gov.in"     # Which API
}
```

## 🎯 Common Use Cases

### Get Current Prices
```python
prices = await agriculture_api_service.get_commodity_prices("Tomato")
```

### State-Specific
```python
prices = await agriculture_api_service.get_commodity_prices(
    commodity="Wheat",
    state="Punjab"
)
```

### Best Price in Region
```python
prices = await agriculture_api_service.get_commodity_prices(
    commodity="Rice",
    state="Haryana",
    district="Karnal"
)

best = max(prices, key=lambda x: x['modal_price'])
print(f"Best: {best['market']} - ₹{best['modal_price']}/qtl")
```

### Average Price
```python
prices = await agriculture_api_service.get_commodity_prices("Onion")
avg = sum(p['modal_price'] for p in prices) / len(prices)
print(f"Average: ₹{avg:.2f}/quintal")
```

## 📝 Logging

```python
import logging
logging.basicConfig(level=logging.INFO)

# You'll see:
# ✅ Successfully fetched X records from eNAM API
# ⚠️ eNAM API returned no data, trying fallback...
# ✅ Successfully fetched X records from fallback API
# ❌ Both APIs failed to return data
```

## ⚙️ Configuration

```python
# .env file
DATA_GOV_API_KEY=your_key_here

# config.py
AGMARKNET_API_BASE = "https://api.data.gov.in/resource"
DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY")
```

## 🧪 Testing

```bash
# Run test suite
cd backend
python test_fallback_api.py
```

## 🔍 Available Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `get_commodity_prices()` | Main method with fallback | List[Dict] |
| `get_daily_mandi_prices()` | Direct mandi API access | List[Dict] |
| `search_mandi_prices()` | Search by commodity/location | List[Dict] |

## 🌾 Common Commodities

| Crop | English | Hindi |
|------|---------|-------|
| 🌾 | Wheat | गेहूं |
| 🌾 | Rice | धान |
| 🌱 | Cotton | कपास |
| 🫘 | Soybean | सोयाबीन |
| 🍅 | Tomato | टमाटर |
| 🧅 | Onion | प्याज |
| 🥔 | Potato | आलू |
| 🌽 | Maize | मक्का |

## ⏱️ Performance

- **Response Time**: 1-3 seconds
- **Timeout**: 10 seconds
- **Retries**: Automatic fallback
- **Cache**: Not implemented (future)

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No data returned | Try without location filters |
| 403 Forbidden | Check API key in .env |
| Timeout | Increase timeout in code |
| Wrong commodity | Try different spellings |

## 📞 Support

- **Mandi Helpline**: 1800-270-0224
- **eNAM**: https://enam.gov.in
- **data.gov.in**: https://data.gov.in

## 🎓 Example Script

```python
import asyncio
from agriculture_apis import agriculture_api_service

async def main():
    # Get wheat prices in Punjab
    wheat_prices = await agriculture_api_service.get_commodity_prices(
        commodity="Wheat",
        state="Punjab"
    )
    
    if wheat_prices:
        print(f"Found {len(wheat_prices)} markets")
        for price in wheat_prices[:5]:
            print(f"{price['market']}: ₹{price['modal_price']}/qtl")
    else:
        print("No data available")

asyncio.run(main())
```

## 📚 Documentation

- **Full Guide**: `MARKET_PRICE_API_GUIDE.md`
- **Summary**: `MARKET_PRICE_API_SUMMARY.md`
- **Quick Ref**: `MARKET_PRICE_QUICK_REF.md` (this file)

---

**Version**: 2.0 | **Updated**: Nov 12, 2025 | **Status**: ✅ Ready
