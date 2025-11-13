/**
 * Persona Detection Engine for Kisaan Suvidha Kendra
 * Analyzes conversation to identify visitor type (farmer, agriculture officer, trader, student, general)
 */

// Persona patterns and keywords for agriculture context
const personaPatterns = {
  farmer: {
    keywords: [
      'farm', 'farmer', 'kheti', 'fasal', 'crop', 'field', 'zameen', 'land',
      'sowing', 'harvest', 'beeज', 'seed', 'fertilizer', 'khad', 'pesticide',
      'disease', 'bimari', 'weather', 'mausam', 'rain', 'barish', 'irrigation',
      'sinchai', 'tractor', 'yield', 'utpadan'
    ],
    questions: [
      'mandi bhav', 'market price', 'crop disease', 'weather forecast',
      'fertilizer', 'pesticide', 'sowing time', 'harvest', 'irrigation',
      'government scheme', 'subsidy', 'kisan yojana'
    ],
    responses: {
      greeting: "Namaste! Main aapki kheti se sambandhit samasya mein madad kar sakta hoon.",
      followup: "Aap kaunsi fasal ugate hain? Mujhe kya jankari chahiye?"
    }
  },
  
  agriculture_officer: {
    keywords: [
      'officer', 'official', 'adhikari', 'government', 'sarkar', 'department',
      'vibhag', 'policy', 'niti', 'scheme', 'yojana', 'subsidy', 'anudan',
      'implementation', 'kriyaanvayan', 'data', 'statistics', 'survey', 'report'
    ],
    questions: [
      'government schemes', 'policy implementation', 'farmer registration',
      'subsidy distribution', 'crop statistics', 'area coverage', 'district data'
    ],
    responses: {
      greeting: "I can assist you with scheme information, farmer data, and policy implementation.",
      followup: "Which scheme or data are you looking for?"
    }
  },
  
  trader: {
    keywords: [
      'trader', 'buyer', 'vyapari', 'merchant', 'wholesale', 'thok', 'mandi',
      'market', 'bazaar', 'price', 'bhav', 'rate', 'commodity', 'purchase',
      'kharid', 'sale', 'bechna', 'quantity', 'matra', 'supply', 'aapurti'
    ],
    questions: [
      'mandi rates', 'wholesale prices', 'commodity availability', 'market trends',
      'supply', 'demand', 'crop procurement', 'bulk purchase'
    ],
    responses: {
      greeting: "I can provide market prices, commodity availability, and trading information.",
      followup: "Which commodity or market are you interested in?"
    }
  },
  
  student: {
    keywords: [
      'student', 'vidyarthi', 'research', 'shodh', 'study', 'adhyayan',
      'university', 'vishwavidyalaya', 'college', 'mahavidyalaya', 'project',
      'pariyojana', 'agriculture science', 'krishi vigyan', 'learning', 'seekhna'
    ],
    questions: [
      'crop science', 'agricultural research', 'farming techniques', 'modern agriculture',
      'internship', 'training', 'workshop', 'study material'
    ],
    responses: {
      greeting: "I can help you with agricultural information for your studies or research.",
      followup: "What topic are you researching or learning about?"
    }
  },
  
  general: {
    keywords: [
      'information', 'jankari', 'help', 'madad', 'about', 'ke bare mein',
      'what', 'kya', 'how', 'kaise', 'where', 'kahan', 'when', 'kab'
    ],
    questions: [
      'services', 'facilities', 'location', 'contact', 'information', 'help'
    ],
    responses: {
      greeting: "Namaste! Main Kisaan Suvidha Kendra ka sahayak hoon. Main aapki madad kar sakta hoon.",
      followup: "Aap kya janna chahte hain?"
    }
  }
}

/**
 * Analyze conversation history to infer persona
 * @param {Array<string>} conversationHistory - Array of user messages
 * @returns {Object} - Persona analysis with confidence scores
 */
export function analyzePersona(conversationHistory) {
  if (!conversationHistory || conversationHistory.length === 0) {
    return {
      persona: 'general',
      confidence: 0,
      allScores: []
    }
  }

  // Combine all conversation into one text for analysis
  const fullConversation = conversationHistory.join(' ').toLowerCase()
  
  // Calculate confidence scores for each persona
  const scores = {}
  
  Object.keys(personaPatterns).forEach(persona => {
    const pattern = personaPatterns[persona]
    let score = 0
    
    // Check keywords with word boundary matching
    pattern.keywords.forEach(keyword => {
      const regex = new RegExp('\\b' + keyword + '\\w*', 'gi')
      const matches = fullConversation.match(regex)
      if (matches) {
        score += matches.length * 0.4 // Count multiple mentions
      }
    })
    
    // Check question patterns (higher weight)
    pattern.questions.forEach(question => {
      if (fullConversation.includes(question)) {
        score += 0.7
      }
    })
    
    scores[persona] = Math.min(1.0, score)
  })
  
  // Find highest confidence persona
  let maxConfidence = 0
  let inferredPersona = 'general'
  
  Object.entries(scores).forEach(([persona, confidence]) => {
    if (confidence > maxConfidence) {
      maxConfidence = confidence
      inferredPersona = persona
    }
  })
  
  // Sort all scores for analysis
  const allScores = Object.entries(scores)
    .map(([persona, confidence]) => ({ persona, confidence }))
    .sort((a, b) => b.confidence - a.confidence)
  
  return {
    persona: inferredPersona,
    confidence: maxConfidence,
    allScores
  }
}

/**
 * Get personalized response based on persona
 * @param {string} persona - Detected persona type
 * @param {string} type - 'greeting' or 'followup'
 * @returns {string} - Personalized response
 */
export function getPersonalizedResponse(persona, type = 'greeting') {
  const pattern = personaPatterns[persona] || personaPatterns.general
  return pattern.responses[type] || pattern.responses.greeting
}

/**
 * Should we infer persona based on conversation length?
 * @param {number} conversationLength - Number of user messages
 * @returns {boolean}
 */
export function shouldInferPersona(conversationLength) {
  return conversationLength >= 2 // After 2 user messages, start inferring
}

/**
 * Get follow-up questions based on current persona inference
 * @param {string} topPersona - Current leading persona
 * @param {number} conversationLength - Length of conversation
 * @returns {string} - Follow-up question
 */
export function getFollowUpQuestion(topPersona, conversationLength) {
  const contextualQuestions = {
    farmer: [
      "Aap kaunsi fasal ugate hain? Kya aapko mandi bhav ya mausam ki jankari chahiye?",
      "Kya aapki fasal mein koi bimari ya samasya hai?",
      "Kya aapko sarkar ki yojanaon ke bare mein janna hai?"
    ],
    agriculture_officer: [
      "Which government scheme or farmer data do you need?",
      "Are you looking for area statistics or subsidy information?",
      "Do you need implementation guidelines or policy details?"
    ],
    trader: [
      "Which mandi or commodity prices are you looking for?",
      "Do you need wholesale rates or supply information?",
      "Are you interested in specific crop availability?"
    ],
    student: [
      "What agricultural topic are you studying?",
      "Are you looking for research data or farming techniques?",
      "Do you need information about modern agriculture practices?"
    ],
    general: [
      "Aap kya jankari chahte hain - mandi bhav, mausam, ya sarkar ki yojana?",
      "Main aapki kaise madad kar sakta hoon?",
      "Kya aap kisaan hain ya vyapari?"
    ]
  }
  
  const questions = contextualQuestions[topPersona] || contextualQuestions.general
  const questionIndex = Math.min(conversationLength - 1, questions.length - 1)
  return questions[questionIndex]
}

export default {
  analyzePersona,
  getPersonalizedResponse,
  shouldInferPersona,
  getFollowUpQuestion,
  personaPatterns
}

