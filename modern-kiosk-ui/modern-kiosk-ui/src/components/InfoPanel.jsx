import { motion } from 'framer-motion'
import { X } from 'lucide-react'
import './InfoPanel.css'

const InfoPanel = ({ panel, onClose }) => {
  const Icon = panel.icon

  return (
    <motion.div
      className="info-panel"
      initial={{ x: 500, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 500, opacity: 0 }}
      transition={{ type: 'spring', damping: 25 }}
    >
      {/* Header */}
      <div className="panel-header">
        <div className="panel-icon">
          <Icon size={24} />
        </div>
        <h3 className="panel-title">{panel.title}</h3>
        <button className="panel-close" onClick={onClose}>
          <X size={20} />
        </button>
      </div>

      {/* Content */}
      <div className="panel-content">
        {/* About Panel */}
        {panel.id === 'about' && (
          <>
            <p className="panel-description">{panel.content.description}</p>
            
            <div className="highlights-section">
              <h4 className="section-title">Highlights</h4>
              <ul className="highlights-list">
                {panel.content.highlights.map((highlight, index) => (
                  <motion.li
                    key={index}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    {highlight}
                  </motion.li>
                ))}
              </ul>
            </div>

            <div className="metrics-grid">
              {panel.content.metrics.map((metric, index) => (
                <motion.div
                  key={index}
                  className="metric-card"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.2 + index * 0.1, type: 'spring' }}
                >
                  <div className="metric-value">{metric.value}</div>
                  <div className="metric-label">{metric.label}</div>
                </motion.div>
              ))}
            </div>
          </>
        )}

        {/* Programs Panel */}
        {panel.id === 'programs' && (
          <div className="programs-section">
            {panel.content.programs.map((program, index) => (
              <motion.div
                key={index}
                className="program-card"
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: index * 0.15 }}
              >
                <h4 className="program-name">{program.name}</h4>
                <p className="program-description">{program.description}</p>
                <div className="program-features">
                  {program.features.map((feature, i) => (
                    <span key={i} className="feature-tag">{feature}</span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Success Stories Panel */}
        {panel.id === 'success' && (
          <>
            <div className="featured-story">
              <h4 className="story-title">{panel.content.featured.title}</h4>
              <p className="story-description">{panel.content.featured.description}</p>
              
              <div className="impact-metrics">
                {panel.content.featured.impact.map((item, index) => (
                  <motion.div
                    key={index}
                    className="impact-item"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2 + index * 0.1, type: 'spring' }}
                  >
                    <div className="impact-value">{item.value}</div>
                    <div className="impact-label">{item.label}</div>
                  </motion.div>
                ))}
              </div>
            </div>

            <div className="overall-impact">
              <h4 className="section-title">Overall Impact</h4>
              <ul className="impact-list">
                {panel.content.overall.map((item, index) => (
                  <motion.li
                    key={index}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.1 * index }}
                  >
                    {item}
                  </motion.li>
                ))}
              </ul>
            </div>
          </>
        )}

        {/* Experience Zone Panel */}
        {panel.id === 'experience' && (
          <div className="sectors-section">
            {panel.content.sectors.map((sector, index) => (
              <motion.div
                key={index}
                className="sector-card"
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: index * 0.15 }}
              >
                <h4 className="sector-name">{sector.name}</h4>
                <ul className="solutions-list">
                  {sector.solutions.map((solution, i) => (
                    <li key={i}>{solution}</li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default InfoPanel




