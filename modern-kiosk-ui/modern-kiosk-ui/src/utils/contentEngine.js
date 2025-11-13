/**
 * Content Engine - Maps user queries to relevant NASSCOM COE content
 * Based on Information_COE_plain.txt
 */

// Structured content database from Information_COE_plain.txt
const contentDatabase = {
  welcome: {
    id: 'welcome',
    title: 'NASSCOM AI & IoT Centre of Excellence',
    subtitle: 'GIFT City, Gandhinagar • Inaugurated by Hon\'ble Chief Minister of Gujarat',
    summary: 'Welcome to India\'s premier deep tech innovation hub. Founded in 2016 through MeitY-State Government-NASSCOM partnership, we\'ve successfully deployed 200+ prototypes across 160+ enterprises.',
    sections: [
      {
        type: 'hero',
        content: 'Deep Tech Innovation for Digital India'
      },
      {
        type: 'stats',
        items: [
          { label: 'Enterprises Engaged', value: '160+' },
          { label: 'Prototypes Developed', value: '200+' },
          { label: 'Successful Deployments', value: '50+' },
          { label: 'Strategic Locations', value: '4 Cities' }
        ]
      },
      {
        type: 'text',
        content: 'Operating from Bangalore, Gurugram, Gandhinagar (GIFT City), and Vizag, we serve as the nation\'s leading deep tech startup accelerator, focusing on IP creation and market development through co-creation and open innovation.'
      },
      {
        type: 'highlights',
        items: [
          'Pan India Deep Tech Startup Growth Enablement',
          'Largest Industry Network for Co-Creation',
          'Global Showcase for India\'s Innovation Story',
          '200+ AI Prototypes • 50+ Market Deployments'
        ]
      }
    ]
  },

  about: {
    id: 'about',
    title: 'About NASSCOM Centre of Excellence',
    subtitle: 'India\'s Premier Deep Tech Innovation Hub',
    summary: 'MeitY COE is one of the most effective enablers of deep tech startup ecosystem focused on IP and Market Creation. Through co-creation and open innovation, we have made these concepts reality in India.',
    sections: [
      {
        type: 'text',
        content: 'The Center of Excellence for IoT & AI emerged from a strategic partnership among MeitY, state governments, and NASSCOM. Founded in July 2016, it marked a pivotal moment within India\'s Digital India Initiative, with a primary focus on democratizing innovation in Internet of Things and AI technologies.'
      },
      {
        type: 'text',
        content: 'Our equipped labs have facilitated the development of prototypes and solutions by startups, tailored specifically to sectors vital for India\'s progress, particularly healthcare and manufacturing. Over the years, we\'ve built unique capabilities to accelerate startups by working with industries and PSUs for successful use case solution development and deployment.'
      },
      {
        type: 'stats',
        items: [
          { label: 'Enterprises Engaged', value: '160+' },
          { label: 'Startups Cocreated With', value: '500+' },
          { label: 'Prototypes Developed', value: '200+' },
          { label: 'Successful Deployments', value: '50+' }
        ]
      },
      {
        type: 'locations',
        items: [
          {
            city: 'Gandhinagar',
            state: 'Gujarat',
            location: 'GIFT City',
            highlight: 'AI COE - Inaugurated Jan 2025'
          },
          {
            city: 'Bangalore',
            state: 'Karnataka',
            location: 'Tech Hub',
            highlight: 'IoT Innovation Center'
          },
          {
            city: 'Gurugram',
            state: 'Haryana',
            location: 'NCR Region',
            highlight: 'Enterprise Connect Hub'
          },
          {
            city: 'Vizag',
            state: 'Andhra Pradesh',
            location: 'Eastern Coast',
            highlight: 'Regional Innovation Center'
          }
        ]
      },
      {
        type: 'achievements',
        title: 'Phase 1 Achievements (2016-2024)',
        items: [
          'Labs operating at close to full occupancy across all locations',
          'Built robust industry connections with over 1,000 enterprises including SMEs',
          'Global showcase for India\'s technological innovations to international visitors',
          'Pioneering thought leadership with over 300 events & workshops hosted',
          'Societal impact through initiatives like Jan Care for public good'
        ]
      },
      {
        type: 'text',
        content: 'After completing our successful first 5-year phase, NASSCOM signed an MoU with Gujarat Informatics Limited, Department of Science and Technology, and Government of Gujarat to establish the AI Center of Excellence at GIFT City, Gandhinagar. The AI COE focuses on sector-specific AI use case development, pilot projects, training for government officials, secure data exchange, and AI model adoption across government departments, private sectors, and MSMEs.'
      },
      {
        type: 'text',
        content: 'The AI COE was inaugurated by the Honourable Chief Minister of Gujarat on 27th January 2025, marking a new chapter in India\'s AI innovation journey.'
      }
    ]
  },

  aiChallenge: {
    id: 'aiChallenge',
    title: 'AI Innovation Challenge',
    subtitle: 'Connecting India\'s Best Startups with Real-World Challenges',
    summary: 'Along with the AI COE inauguration, the Honourable Chief Minister of Gujarat launched the AI Innovation Challenge to connect India\'s leading AI and deep-tech startups with real-world challenges from public and private sectors.',
    sections: [
      {
        type: 'text',
        content: 'The AI Innovation Challenge (AI-IC) provides a unique opportunity for India\'s leading AI and deep-tech startups to showcase their cutting-edge solutions, collaborate with key stakeholders, and create meaningful impact in agriculture, healthcare, manufacturing, governance, and beyond.'
      },
      {
        type: 'text',
        content: 'By focusing on structured collaboration and outcome-focused innovation, AI-IC creates the necessary conditions for scalable AI adoption. For government, it enables more responsive governance. For industry, it offers a competitive edge through smarter operations. For startups, it becomes a proving ground with direct access to implementation opportunities.'
      },
      {
        type: 'list',
        title: 'Target Sectors',
        items: [
          '🌾 Agriculture - Smart farming, crop monitoring, quality assessment',
          '🏥 Healthcare - Medical imaging, diagnostics, patient monitoring',
          '⚙️ Manufacturing - Quality inspection, predictive maintenance, automation',
          '🏛️ Governance - Public services, citizen engagement, smart governance',
          'Additional sectors including education, transportation, and more'
        ]
      },
      {
        type: 'text',
        content: 'The platform is promoted through AI COE, DST, and GIL websites and social media, encouraging startups to apply with their innovation solutions to address real-world use cases.'
      },
      {
        type: 'criteria',
        title: 'Eligibility Criteria for Startups',
        items: [
          'Innovators and Mature Startups across the Nation',
          'Deep-tech capabilities and Market-ready Digital Solutions',
          'Annual turnover not exceeding ₹25 crore',
          'Period of existence not exceeding 10 years from Date of Incorporation',
          'Total manpower not more than 100 employees'
        ]
      },
      {
        type: 'text',
        content: 'Applications from startups are reviewed for selection to provide solutions and develop Proof of Concepts (PoCs) for the use cases. For more information, visit: https://gujarat.coe-iot.com/ai-coe-ai-innovation-challenge/'
      }
    ]
  },

  growx: {
    id: 'growx',
    title: 'GrowX Acceleration Program',
    subtitle: 'Complete Startup Acceleration Ecosystem',
    summary: 'GrowX is COE flagship acceleration program that runs to accelerate deep tech startups. It provides comprehensive support including Computing Infrastructure, Co-Working Space, AI Experience Zone, GTM Support, Funding up to 25 lakhs rupees, Mentorship, and Solution Showcase Opportunities.',
    sections: [
      {
        type: 'text',
        content: 'GrowX provides various benefits to accelerate deep tech startups, including state-of-the-art computing infrastructure, co-working spaces, AI experience zones, go-to-market support, funding assistance, expert mentorship, and solution showcase opportunities.'
      },
      {
        type: 'benefits',
        title: 'Complete Acceleration Ecosystem',
        items: [
          '🖥️ Computing Infrastructure - AI/ML labs with V100 GPUs and advanced hardware',
          '🏢 Co-Working Space - Modern facilities and collaborative environment',
          'AI Experience Zone - Showcase and demo cutting-edge solutions',
          '📈 Go-To-Market Support - Business development and market entry assistance',
          '💰 Funding Support - Up to ₹25 lakhs for product development and scaling',
          '👥 Expert Mentorship - Panel of industry veterans and domain experts',
          'Solution Showcase - Opportunities at events, expos, and industry gatherings'
        ]
      },
      {
        type: 'text',
        content: 'COE conducts Innovation masterclasses for startups to educate themselves on critical subjects including Intellectual Property Rights, Investment Funding, Cloud Computing, Product-Market Fit, Design Validation, and more.'
      },
      {
        type: 'text',
        content: 'We are building a comprehensive panel of mentors who can guide startups through their entire growth journey - from product-market fit and design validation to fund raising, valuation assessment, market reach strategies, and scaling operations. Mentor details are hosted on our website for startups to request personalized sessions.'
      }
    ]
  },

  successStories: {
    id: 'successStories',
    title: 'Success Stories',
    subtitle: 'AI-Powered Grain Quality Assessment',
    summary: 'Our flagship success: AI-powered grain quality inspection system deployed at APMCs in Gujarat, empowering 1000+ farmers and facilitating ₹700+ crore grain trade.',
    sections: [
      {
        type: 'case-study',
        title: 'AI Grain Quality Assessment',
        problem: 'Grain quality evaluation relies on manual and subjective inspection, leading to inconsistent results, lack of transparency, and unfair pricing for farmers.',
        solution: 'AI-based grain quality assessment system capable of evaluating over ten physical parameters of grains (broken grains, foreign materials etc.) within 30 seconds using computer vision.',
        impact: [
          'Deployed at APMCs in Kheda and Anand in Gujarat',
          'Empowered over 1,000 farmers',
          'Facilitated grain trade worth ₹700+ crore',
          'Ensures fair pricing and reduces losses from rejections'
        ]
      },
      {
        type: 'stats',
        items: [
          { label: 'Farmers Empowered', value: '1000+' },
          { label: 'Trade Value', value: '₹700+ Cr' },
          { label: 'Evaluation Time', value: '30 sec' },
          { label: 'Parameters Checked', value: '10+' }
        ]
      }
    ]
  },

  experienceZone: {
    id: 'experienceZone',
    title: 'AI Experience Zone',
    subtitle: 'Cutting-Edge AI Solutions Showcase',
    summary: 'Our AI Experience Zone houses cutting edge AI solutions made by deep tech startups, showcasing real world applications of AI in Healthcare, Manufacturing, Agriculture, and Safety.',
    sections: [
      {
        type: 'sectors',
        title: 'Solution Areas',
        items: [
          {
            icon: '🏥',
            name: 'Healthcare',
            solutions: ['Medical Imaging Analysis', 'Patient Monitoring Systems', 'AI Diagnostics']
          },
          {
            icon: '⚙️',
            name: 'Manufacturing',
            solutions: ['AI Quality Inspection', 'Predictive Maintenance', 'IoT Machine Monitoring']
          },
          {
            icon: '🌾',
            name: 'Agriculture',
            solutions: ['Grain Quality Assessment', 'Crop Monitoring', 'Smart Farming IoT']
          },
          {
            icon: '🛡️',
            name: 'Safety',
            solutions: ['Video Analytics', 'Anomaly Detection', 'Smart Surveillance']
          }
        ]
      },
      {
        type: 'text',
        content: 'The zone is used to make industries, govt. officials, MSMEs and other stakeholders aware about real world applications of AI in different sectors.'
      }
    ]
  },

  industry: {
    id: 'industry',
    title: 'Industry Digitalization',
    subtitle: 'Smart Manufacturing for MSMEs',
    summary: 'AI COE makes significant efforts to digitalize MSMEs with Industry 4.0 and smart manufacturing solutions including IoT machine monitoring, AI quality inspection, and QR code-based inventory tracking.',
    sections: [
      {
        type: 'text',
        content: 'AI COE makes significant efforts to digitalize the MSMEs with Industry 4.0 and smart manufacturing solutions.'
      },
      {
        type: 'solutions',
        title: 'Smart Solutions',
        items: [
          'IoT for Machine monitoring',
          'AI for Quality inspection',
          'QR code-based track and trace of inventory'
        ]
      },
      {
        type: 'achievements',
        title: 'Impact',
        items: [
          'Educated over thousand MSMEs on adoption of smart solutions',
          'Partnered with Quality Council of India',
          'Conducted workshops in 12 different Industrial Clusters',
          'Part of Gujarat Gunvatta Yatra initiative',
          'Collaborated with Industry Associations: NPC, GCCI, GSPMA, SGCCI'
        ]
      }
    ]
  },

  incentives: {
    id: 'incentives',
    title: 'Gujarat IT/ITeS Policy Incentives',
    subtitle: 'Support for Deep Tech Startups',
    summary: 'Gujarat Government offers substantial incentives for Deep Tech Startups including R&D support (25% up to ₹25L), Patent assistance (75% up to ₹10L), Quality certification (50% up to ₹5L), and Cloud/Infrastructure support (35% up to ₹10L).',
    sections: [
      {
        type: 'incentives',
        title: 'Available Incentives',
        items: [
          {
            name: 'R&D, Prototype & Product Development',
            value: '25% up to ₹25 Lakhs',
            description: 'One time support for expenses on R&D, creating prototypes, and developing products'
          },
          {
            name: 'Patent Assistance',
            value: '75% up to ₹5L (Domestic) / ₹10L (International)',
            description: 'Maximum of 10 patents per year for five years. Includes Government and professional fees'
          },
          {
            name: 'Quality Certification',
            value: '50% up to ₹5 Lakhs per certificate',
            description: 'Subvention for up to three quality certifications'
          },
          {
            name: 'Cloud & Infrastructure',
            value: '35% up to ₹10 Lakhs',
            description: 'Support for internet bandwidth and cloud platform costs for 6 months'
          },
          {
            name: 'Lease Rental Support',
            value: '₹25/sq.ft or ₹1250/seat per month',
            description: 'Support for office space rental for five years'
          }
        ]
      }
    ]
  },

  location: {
    id: 'location',
    title: 'Our Locations',
    subtitle: '4 Strategic Centers Across India',
    summary: 'NASSCOM COE operates from 4 strategic locations across India: Bangalore, Gurugram, Gandhinagar (GIFT City), and Vizag, serving as pivotal resources for entrepreneurs in emerging technologies.',
    sections: [
      {
        type: 'locations',
        items: [
          {
            city: 'Gandhinagar',
            state: 'Gujarat',
            location: 'GIFT City',
            highlight: 'AI COE - Inaugurated Jan 2025'
          },
          {
            city: 'Bangalore',
            state: 'Karnataka',
            location: 'Tech Hub',
            highlight: 'IoT Innovation Center'
          },
          {
            city: 'Gurugram',
            state: 'Haryana',
            location: 'NCR Region',
            highlight: 'Enterprise Connect Hub'
          },
          {
            city: 'Vizag',
            state: 'Andhra Pradesh',
            location: 'Eastern Coast',
            highlight: 'Regional Innovation Center'
          }
        ]
      },
      {
        type: 'text',
        content: 'Each location is equipped with state-of-the-art labs, co-working spaces, and facilities to support startup growth and innovation.'
      }
    ]
  }
}

// Keyword mapping for query matching
const queryKeywords = {
  welcome: ['welcome', 'hello', 'hi', 'start', 'about you'],
  about: ['about', 'what is', 'tell me about', 'information', 'overview', 'history'],
  aiChallenge: ['challenge', 'innovation challenge', 'competition', 'use case', 'apply'],
  growx: ['growx', 'program', 'acceleration', 'incubation', 'funding', 'mentorship', 'support'],
  successStories: ['success', 'story', 'impact', 'grain', 'farmer', 'achievement', 'case study'],
  experienceZone: ['experience', 'zone', 'demo', 'showcase', 'solutions', 'see', 'visit'],
  industry: ['industry', 'msme', 'manufacturing', 'digitalization', 'smart manufacturing'],
  incentives: ['incentive', 'policy', 'subsidy', 'government', 'support', 'benefit', 'grant'],
  location: ['location', 'where', 'address', 'office', 'center', 'city']
}

/**
 * Get content for a user query
 * @param {string} query - User's question or query
 * @returns {object} - Relevant content slide
 */
export function getContentForQuery(query) {
  if (!query || query.trim() === '') {
    return contentDatabase.welcome
  }

  const lowerQuery = query.toLowerCase()
  
  // Find best matching content
  let bestMatch = 'welcome'
  let maxScore = 0

  for (const [contentKey, keywords] of Object.entries(queryKeywords)) {
    let score = 0
    keywords.forEach(keyword => {
      if (lowerQuery.includes(keyword)) {
        score += keyword.length // Longer keywords get more weight
      }
    })
    
    if (score > maxScore) {
      maxScore = score
      bestMatch = contentKey
    }
  }

  return contentDatabase[bestMatch] || contentDatabase.welcome
}

/**
 * Get all available content
 * @returns {object} - All content in database
 */
export function getAllContent() {
  return contentDatabase
}

/**
 * Get content by ID
 * @param {string} id - Content ID
 * @returns {object} - Content object
 */
export function getContentById(id) {
  return contentDatabase[id] || contentDatabase.welcome
}

