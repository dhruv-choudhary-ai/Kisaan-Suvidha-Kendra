# 🚀 Kisaan Agent Quick Reference Guide

## 16 Specialized Agricultural Agents

### 1. 🌱 Fertilizer Recommendation Agent
**Triggers:** "which fertilizer", "fertilizer for", "NPK", "urea", "DAP", nutrient deficiency  
**Provides:** Specific fertilizer names, NPK ratios, quantities (kg/acre), costs, organic alternatives  
**Example:** "गेहूं में कौन सा उर्वरक डालें?" → Recommends Urea 50kg + DAP 25kg with exact costs

### 2. 🐛 Pesticide Recommendation Agent
**Triggers:** "which pesticide", "pest control", "insecticide", "fungicide", IPM  
**Provides:** Chemical + organic options, dosages, PHI/REI, safety measures  
**Example:** "टमाटर में कीड़े लगे हैं" → IPM strategy + specific pesticides with safety protocols

### 3. 📋 Application Guide Agent
**Triggers:** "how to apply", "dosage", "quantity", "how much", spray timing  
**Provides:** Step-by-step mixing, dosage calculations, spray techniques, safety  
**Example:** "यूरिया कैसे डालना है?" → Complete mixing instructions with exact quantities

### 4. 📅 Fertilizer Schedule Planner Agent
**Triggers:** "fertilizer schedule", "when to apply fertilizer", stage-wise fertilization  
**Provides:** Complete season calendar, basal + top dressing timings, costs  
**Example:** "धान की पूरी खाद अनुसूची" → Month-by-month fertilization plan

### 5. 💧 Irrigation Management Agent
**Triggers:** "watering", "drip irrigation", "water management", irrigation scheduling  
**Provides:** Critical stages, drip vs flood comparison, water conservation, subsidies  
**Example:** "टमाटर को पानी कब देना चाहिए?" → Stage-wise irrigation schedule + subsidy info

### 6. 🌍 Soil Health Agent
**Triggers:** "soil pH", "soil testing", "soil improvement", soil amendments  
**Provides:** Testing locations, pH correction, organic matter, nutrient management  
**Example:** "मिट्टी की जांच कहां करवाएं?" → Free govt labs + soil improvement strategies

### 7. 📆 Crop Calendar Agent
**Triggers:** "when to sow", "planting calendar", "harvest time", crop lifecycle  
**Provides:** Month-by-month activities, sowing to harvest, complete economics  
**Example:** "गेहूं की बुवाई से कटाई तक" → Complete 6-month calendar with costs

### 8. 💰 Input Cost Calculator Agent
**Triggers:** "input costs", "ROI", "profit calculation", budget planning  
**Provides:** Complete cost breakdown, profit scenarios, financing options  
**Example:** "धान में कितना खर्च आएगा?" → Detailed ₹22,500/acre breakdown + ROI

### 9. 🚨 Emergency Response Agent
**Triggers:** "urgent", "pest outbreak", "disease emergency", crop failure, disaster  
**Provides:** Immediate actions (2-4 hrs), emergency contacts, damage control  
**Example:** "खेत में अचानक कीड़े आ गए" → Immediate spray + emergency helpline 1800-180-1551

### 10. 👨‍🌾 Local Expert Connection Agent
**Triggers:** "contact expert", "agricultural officer", "KVK", need human help  
**Provides:** Kisan Call Center, district offices, KVK finder, app resources  
**Example:** "कृषि विशेषज्ञ से बात करनी है" → 1800-180-1551 + local KVK details

### 11. 🌾 Crop Selection Agent
**Triggers:** "which crop", "what to grow", "should I plant", "best crop for"  
**Provides:** Seasonal recommendations, market demand, profitability  
**Example:** "इस मौसम में क्या लगाएं?" → 2-3 rabi crops with reasons + timeline

### 12. 🍃 Crop Disease Agent
**Triggers:** Disease symptoms, pests, yellow leaves, spots, wilting  
**Provides:** Camera trigger for visual diagnosis  
**Example:** "पत्तियों में धब्बे हैं" → Triggers camera for accurate diagnosis

### 13. 🌤️ Weather Advisory Agent
**Triggers:** "weather", "rain", "temperature for farming"  
**Provides:** Current weather + farming advice, warnings  
**Example:** "आज मौसम कैसा रहेगा?" → Temp 25°C, 60% humidity → Ideal for spraying

### 14. 💵 Market Price Agent
**Triggers:** "price", "rate", "mandi", "bhav"  
**Provides:** eNAM + data.gov.in prices, best markets, selling strategy  
**Example:** "गेहूं का भाव क्या है?" → ₹2,150/quintal, 5 mandis, best prices

### 15. 🏛️ Government Schemes Agent
**Triggers:** "scheme", "subsidy", "loan", "PM-Kisan", "insurance", "योजना"  
**Provides:** Detailed scheme info, eligibility, how to apply, contacts  
**Example:** "PM-Kisan योजना बताएं" → ₹6000/year, eligibility, application process

### 16. 🤝 General Advisory Agent
**Triggers:** Other farming questions not matching above  
**Provides:** Comprehensive farming advice, general guidance  
**Example:** "खेती कैसे करें?" → General farming best practices

---

## 📞 Emergency Contacts (Available 24x7)

| Service | Number | Purpose |
|---------|--------|---------|
| **Kisan Call Center** | **1800-180-1551** | All farming queries, 24x7 |
| eNAM Market | 1800-270-0224 | Market prices, trading |
| Crop Insurance (PMFBY) | 1800-180-1551 | Report damage in 72 hrs |
| IMD Weather | 1800-102-2022 | Disaster warnings |

---

## 🎯 Query Classification Rules

The **Query Understanding Agent** classifies based on keywords:

| Agent Type | Keywords |
|------------|----------|
| **fertilizer_recommendation** | "which fertilizer", "fertilizer for", "NPK", "urea", "DAP", "nutrient deficiency" |
| **pesticide_recommendation** | "which pesticide", "pest control", "insecticide", "fungicide", "IPM" |
| **application_guide** | "how to apply", "dosage", "quantity", "how much", "spray timing" |
| **fertilizer_schedule** | "fertilizer schedule", "when to apply fertilizer", "stage-wise" |
| **irrigation_management** | "watering", "drip irrigation", "water management", "irrigation scheduling" |
| **soil_health** | "soil pH", "soil testing", "soil improvement", "soil amendments" |
| **crop_calendar** | "when to sow", "planting calendar", "harvest time", "crop lifecycle" |
| **cost_calculation** | "input costs", "ROI", "profit calculation", "budget planning" |
| **emergency_response** | "urgent", "pest outbreak", "disease emergency", "crop failure" |
| **expert_connection** | "contact expert", "agricultural officer", "KVK", "need help" |
| **crop_selection** | "which crop", "what to grow", "should I plant", "best crop" |
| **crop_disease** | disease symptoms, "yellow leaves", "spots", "wilting", "rotten" |
| **weather_advisory** | "weather", "rain", "temperature", "मौसम" |
| **market_price** | "price", "rate", "mandi", "bhav", "भाव" |
| **government_schemes** | "scheme", "subsidy", "loan", "PM-Kisan", "insurance", "योजना" |
| **general_advisory** | Everything else |

---

## 💡 Pro Tips for Best Results

### 1. **Be Specific**
❌ "खाद चाहिए"  
✅ "गेहूं की फसल में कौन सा उर्वरक डालना चाहिए?"

### 2. **Mention Crop**
❌ "कीड़े लगे हैं"  
✅ "टमाटर में कीड़े लगे हैं, कौन सी दवा डालूं?"

### 3. **Include Growth Stage** (if relevant)
✅ "धान में फूल आने पर कौन सा उर्वरक दें?"

### 4. **For Emergencies, Use Keywords**
✅ "खेत में अचानक बहुत सारे कीड़े आ गए हैं, क्या करूं?" → Triggers emergency agent

### 5. **For Cost Info**
✅ "गेहूं की खेती में प्रति एकड़ कितना खर्च आएगा?" → Detailed cost breakdown

---

## 🔄 Agent Flow Example

```
User: "गेहूं में पीले पत्ते हो रहे हैं, कौन सा उर्वरक दूं?"
    ↓
Query Understanding Agent
    Detects: fertilizer query + nutrient deficiency symptom
    Routes to → fertilizer_recommendation
    ↓
Fertilizer Recommendation Agent
    Analyzes: Wheat + yellow leaves → Nitrogen deficiency
    Recommends:
      • Urea (46-0-0): 50 kg/acre
      • Cost: ₹350
      • Application: Top dressing + irrigation
      • Expected improvement: 7-10 days
    ↓
Response Generation
    Formats response in Hindi with:
      • Specific fertilizer names
      • Exact quantities and costs
      • Application method
      • Timeline
    ↓
User receives comprehensive answer!
```

---

## 📊 Success Metrics

Each agent provides:

✅ **Specific numbers** (50 kg/acre, not "adequate")  
✅ **Exact costs** (₹350/bag, not "affordable")  
✅ **Clear timings** (15 days after sowing, not "early stage")  
✅ **Real products** (Urea 46-0-0, not just "nitrogen fertilizer")  
✅ **Safety info** (for chemicals)  
✅ **Contact numbers** (for expert help)  
✅ **Subsidy information** (where applicable)

---

## 🧪 Testing Commands

```bash
# Test all agents (comprehensive)
python test_all_agents.py

# Test specific agent
python test_all_agents.py fertilizer_recommendation
python test_all_agents.py emergency_response
python test_all_agents.py cost_calculation

# Test edge cases
python test_all_agents.py --edge
```

---

## 🌟 Agent Selection Priority

When query matches multiple agents:

1. **Emergency keywords** → Emergency Response Agent (highest priority)
2. **Specific need** → Specialized agent (e.g., fertilizer, pesticide)
3. **General questions** → General Advisory Agent (fallback)

---

## 📱 Integration Points

### External APIs Used:
- **OpenWeatherMap** → Weather Advisory Agent
- **eNAM API** → Market Price Agent (primary)
- **data.gov.in API** → Market Price Agent (fallback)
- **Government databases** → Government Schemes Agent

### Future Integrations:
- Soil testing labs API
- KVK expert database
- E-commerce platforms
- Payment gateways (for inputs)

---

**🌾 Made with ❤️ for Indian Farmers 🌾**
