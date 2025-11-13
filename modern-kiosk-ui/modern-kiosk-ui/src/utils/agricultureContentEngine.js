/**
 * Agriculture Content Engine - Maps farmer queries to relevant agricultural content
 * For Kisaan Suvidha Kendra
 */

// Structured agricultural content database
const agricultureContent = {
  welcome: {
    id: 'welcome',
    title: 'किसान सुविधा केंद्र | Kisaan Suvidha Kendra',
    subtitle: 'आपके खेती के सवालों का समाधान | Your Agricultural Assistant',
    summary: 'नमस्ते! मैं आपकी खेती से जुड़े सभी सवालों में मदद के लिए यहाँ हूँ। Welcome! I am here to help with all your farming questions including crop advisory, weather updates, market prices, government schemes, and disease diagnosis.',
    sections: [
      {
        type: 'hero',
        content: 'Smart Farming Solutions for Indian Farmers'
      },
      {
        type: 'stats',
        items: [
          { label: 'Languages Supported', value: '9+' },
          { label: 'Crop Varieties', value: '100+' },
          { label: 'Daily Market Updates', value: '500+ Markets' },
          { label: 'Government Schemes', value: '50+' }
        ]
      },
      {
        type: 'services',
        title: 'हम आपकी कैसे मदद कर सकते हैं? | How can we help you?',
        items: [
          '🌾 फसल सलाह | Crop Advisory',
          '🌡️ मौसम की जानकारी | Weather Information', 
          '💰 बाजार भाव | Market Prices',
          '🏛️ सरकारी योजनाएं | Government Schemes',
          '🐛 रोग निदान | Disease Diagnosis',
          '💧 सिंचाई सलाह | Irrigation Guidance'
        ]
      }
    ]
  },

  cropAdvisory: {
    id: 'cropAdvisory',
    title: 'फसल सलाह | Crop Advisory',
    subtitle: 'Expert Guidance for Better Yields',
    summary: 'Get personalized advice on crop selection, sowing time, fertilizer application, pest management, and harvest timing based on your location and soil type.',
    sections: [
      {
        type: 'list',
        title: 'Main Advisory Areas',
        items: [
          '🌱 Crop Selection - Best crops for your soil and season',
          '📅 Sowing Calendar - Optimal timing for maximum yield',
          '🧪 Fertilizer Schedule - NPK recommendations',
          '💧 Irrigation Planning - Water management strategies',
          '🐛 Pest Management - Integrated pest control solutions',
          '📊 Yield Estimation - Expected output planning'
        ]
      },
      {
        type: 'text',
        content: 'Our AI-powered system analyzes your location, soil type, weather patterns, and crop history to provide customized recommendations for optimal farming results.'
      }
    ]
  },

  weather: {
    id: 'weather',
    title: 'मौसम की जानकारी | Weather Information',
    subtitle: 'Real-time Weather Updates & Forecasts',
    summary: 'Get current weather conditions, 7-day forecasts, rainfall predictions, and weather-based farming advisories for your location.',
    sections: [
      {
        type: 'list',
        title: 'Weather Services',
        items: [
          '🌡️ Temperature & Humidity - Current conditions',
          '🌧️ Rainfall Forecast - 7-day predictions',
          '💨 Wind Speed - Impact on crop management',
          '⚠️ Weather Alerts - Extreme conditions warning',
          '📊 Historical Data - Season comparisons',
          '🌾 Farming Advisory - Weather-based recommendations'
        ]
      },
      {
        type: 'text',
        content: 'Timely weather information helps you plan farming activities like sowing, irrigation, fertilizer application, and harvesting to maximize yield and minimize losses.'
      }
    ]
  },

  marketPrices: {
    id: 'marketPrices',
    title: 'बाजार भाव | Market Prices',
    subtitle: 'Daily Mandi Rates Across India',
    summary: 'Check current market prices for crops across 500+ mandis in India. Get minimum, maximum, and modal prices to make informed selling decisions.',
    sections: [
      {
        type: 'stats',
        items: [
          { label: 'Markets Covered', value: '500+' },
          { label: 'Daily Updates', value: 'Real-time' },
          { label: 'Commodities', value: '100+' },
          { label: 'States', value: 'All India' }
        ]
      },
      {
        type: 'list',
        title: 'Market Information',
        items: [
          '💰 Current Prices - Min, Max, Modal rates',
          '📊 Price Trends - 30-day analysis',
          '🏛️ Government MSP - Support prices',
          '📍 Nearby Markets - Distance & rates comparison',
          '📈 Best Selling Time - Price predictions',
          '🚚 Transport Costs - Logistics planning'
        ]
      }
    ]
  },

  govSchemes: {
    id: 'govSchemes',
    title: 'सरकारी योजनाएं | Government Schemes',
    subtitle: 'Farmer Welfare Programs & Subsidies',
    summary: 'Explore 50+ central and state government schemes including PM-KISAN, crop insurance, subsidy programs, and loan schemes. Get eligibility criteria and application procedures.',
    sections: [
      {
        type: 'schemes',
        title: 'Major Schemes',
        items: [
          {
            name: 'PM-KISAN',
            description: '₹6000/year direct benefit transfer to all farmer families',
            benefit: '₹2000 every 4 months'
          },
          {
            name: 'Pradhan Mantri Fasal Bima Yojana',
            description: 'Crop insurance against natural calamities',
            benefit: 'Up to 90% premium subsidy'
          },
          {
            name: 'Kisan Credit Card',
            description: 'Easy agricultural loans at 4% interest',
            benefit: 'Up to ₹3 Lakhs credit'
          },
          {
            name: 'Soil Health Card Scheme',
            description: 'Free soil testing and nutrient management',
            benefit: 'Customized fertilizer recommendations'
          }
        ]
      },
      {
        type: 'text',
        content: 'Ask about any specific scheme to know eligibility criteria, required documents, application process, and benefits you can receive.'
      }
    ]
  },

  diseaseDetection: {
    id: 'diseaseDetection',
    title: 'रोग निदान | Disease Detection',
    subtitle: 'AI-Powered Crop Disease Diagnosis',
    summary: 'Use your phone camera to capture leaf images and get instant AI-powered disease diagnosis with treatment recommendations in your language.',
    sections: [
      {
        type: 'how-it-works',
        title: 'How It Works',
        steps: [
          '1. Capture clear image of affected plant leaf',
          '2. AI analyzes symptoms and identifies disease',
          '3. Get diagnosis with severity assessment',
          '4. Receive treatment recommendations',
          '5. Learn preventive measures'
        ]
      },
      {
        type: 'list',
        title: 'Supported Crops',
        items: [
          '🌾 Wheat, Rice, Maize, Bajra',
          '🥔 Potato, Tomato, Onion',
          '🫘 Cotton, Soybean, Groundnut',
          '🌶️ Chilli, Brinjal, Okra',
          '🍇 Grapes, Pomegranate'
        ]
      },
      {
        type: 'text',
        content: 'Early detection and proper treatment can save up to 30-40% of potential crop loss. Use this feature regularly to monitor your crop health.'
      }
    ]
  },

  fertilizer: {
    id: 'fertilizer',
    title: 'उर्वरक सलाह | Fertilizer Recommendations',
    subtitle: 'Balanced Nutrition for Better Yields',
    summary: 'Get soil-based fertilizer recommendations including NPK ratios, micronutrients, organic manure, and application schedules for your crops.',
    sections: [
      {
        type: 'list',
        title: 'Fertilizer Services',
        items: [
          '🧪 NPK Recommendations - Based on soil test results',
          '🌿 Organic Alternatives - Vermicompost, FYM usage',
          '💊 Micronutrients - Zinc, Boron, Iron supplements',
          '📅 Application Schedule - When and how much',
          '💰 Cost Optimization - Best value products',
          '🎯 Subsidy Information - Government support'
        ]
      }
    ]
  },

  irrigation: {
    id: 'irrigation',
    title: 'सिंचाई सलाह | Irrigation Guidance',
    subtitle: 'Water Management for Optimal Growth',
    summary: 'Learn about drip irrigation, sprinkler systems, water scheduling, and conservation techniques to use water efficiently and reduce costs.',
    sections: [
      {
        type: 'list',
        title: 'Irrigation Methods',
        items: [
          '💧 Drip Irrigation - 40-60% water savings',
          '🌊 Sprinkler System - Uniform water distribution',
          '📅 Irrigation Schedule - Crop-specific timing',
          '💰 Subsidy Schemes - 50-80% government support',
          '⚡ Solar Pumps - Energy-efficient solutions',
          '💦 Rainwater Harvesting - Conservation techniques'
        ]
      }
    ]
  },

  soilHealth: {
    id: 'soilHealth',
    title: 'मिट्टी परीक्षण | Soil Health',
    subtitle: 'Know Your Soil, Grow Better',
    summary: 'Get free soil testing through government schemes. Understand pH levels, nutrient content, and get customized fertilizer recommendations.',
    sections: [
      {
        type: 'list',
        title: 'Soil Health Services',
        items: [
          '🧪 Free Soil Testing - Government labs',
          '📊 Soil Health Card - Digital records',
          '⚖️ pH Management - Lime/gypsum recommendations',
          '🌿 Organic Matter - Improvement strategies',
          '💧 Water Retention - Soil improvement tips',
          '🌾 Crop Rotation - Soil fertility management'
        ]
      }
    ]
  },

  emergency: {
    id: 'emergency',
    title: 'आपातकालीन सहायता | Emergency Support',
    subtitle: 'Immediate Help & Expert Contacts',
    summary: 'Get immediate assistance for pest attacks, disease outbreaks, or natural calamities. Contact agricultural officers and experts.',
    sections: [
      {
        type: 'contacts',
        title: 'Emergency Contacts',
        items: [
          '📞 Kisan Call Center: 1800-180-1551',
          '🏛️ District Agriculture Officer',
          '🌾 Krishi Vigyan Kendra (KVK)',
          '🐛 Pest Control Experts',
          '📱 WhatsApp Helpline',
          '🏥 Veterinary Emergency'
        ]
      }
    ]
  }
}

// Keyword mapping for agricultural queries
const queryKeywords = {
  welcome: ['welcome', 'hello', 'hi', 'namaste', 'start', 'help'],
  cropAdvisory: ['crop', 'sowing', 'fasal', 'kheti', 'boya', 'advisory', 'recommendation'],
  weather: ['weather', 'mausam', 'rain', 'barish', 'temperature', 'forecast'],
  marketPrices: ['price', 'bhav', 'mandi', 'market', 'rate', 'selling'],
  govSchemes: ['scheme', 'yojana', 'subsidy', 'government', 'pm kisan', 'insurance'],
  diseaseDetection: ['disease', 'rog', 'bimari', 'pest', 'keet', 'diagnosis', 'camera'],
  fertilizer: ['fertilizer', 'khad', 'urvarak', 'npk', 'manure', 'organic'],
  irrigation: ['irrigation', 'sinchai', 'water', 'pani', 'drip', 'sprinkler'],
  soilHealth: ['soil', 'mitti', 'testing', 'parikshan', 'ph', 'health card'],
  emergency: ['emergency', 'urgent', 'help', 'contact', 'officer', 'expert']
}

/**
 * Get content for a farmer's query
 * @param {string} query - Farmer's question
 * @param {object} responseData - Additional data from backend
 * @returns {object} - Relevant content slide
 */
export function getAgricultureContent(query, responseData = null) {
  if (!query || query.trim() === '') {
    return agricultureContent.welcome
  }

  const lowerQuery = query.toLowerCase()
  
  // If backend provides specific content type
  if (responseData && responseData.query_type) {
    const contentMap = {
      'crop_disease': 'diseaseDetection',
      'weather': 'weather',
      'market_price': 'marketPrices',
      'government_scheme': 'govSchemes',
      'crop_advisory': 'cropAdvisory',
      'fertilizer': 'fertilizer',
      'irrigation': 'irrigation',
      'soil_health': 'soilHealth'
    }
    
    const mappedContent = contentMap[responseData.query_type]
    if (mappedContent && agricultureContent[mappedContent]) {
      return agricultureContent[mappedContent]
    }
  }

  // Find best matching content based on keywords
  let bestMatch = 'welcome'
  let maxScore = 0

  for (const [contentKey, keywords] of Object.entries(queryKeywords)) {
    let score = 0
    keywords.forEach(keyword => {
      if (lowerQuery.includes(keyword)) {
        score += keyword.length
      }
    })
    
    if (score > maxScore) {
      maxScore = score
      bestMatch = contentKey
    }
  }

  return agricultureContent[bestMatch] || agricultureContent.welcome
}

/**
 * Get all agricultural content
 */
export function getAllAgricultureContent() {
  return agricultureContent
}

/**
 * Get content by ID
 */
export function getAgricultureContentById(id) {
  return agricultureContent[id] || agricultureContent.welcome
}

// Export for backward compatibility
export const getContentForQuery = getAgricultureContent
export const getAllContent = getAllAgricultureContent
export const getContentById = getAgricultureContentById
