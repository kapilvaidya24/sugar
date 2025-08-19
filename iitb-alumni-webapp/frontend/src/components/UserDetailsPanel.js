import React from 'react';
import './UserDetailsPanel.css';

const UserDetailsPanel = ({ user, isOpen, onClose }) => {
  if (!isOpen || !user) return null;

  const formatYear = (year) => year ? year.toString() : 'Present';
  
  const getJobDuration = (job) => {
    if (job.start_year && job.end_year) {
      const duration = job.end_year - job.start_year;
      return duration > 0 ? `${duration} year${duration !== 1 ? 's' : ''}` : '< 1 year';
    }
    if (job.start_year && !job.end_year) {
      const current_year = new Date().getFullYear();
      const duration = current_year - job.start_year;
      return `${duration} year${duration !== 1 ? 's' : ''} (ongoing)`;
    }
    return '';
  };

  return (
    <div className={`user-details-overlay ${isOpen ? 'open' : ''}`}>
      <div className="user-details-panel">
        <div className="panel-header">
          <div className="user-header">
            <h2 className="user-name">{user.name}</h2>
            <div className="user-meta">
              {user.grad_yr && <span className="grad-year">Class of {user.grad_yr}</span>}
              {user.link_ln && (
                <a 
                  href={user.link_ln} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="linkedin-profile"
                >
                  LinkedIn Profile →
                </a>
              )}
            </div>
          </div>
          <button 
            onClick={onClose}
            className="close-button"
          >
            ×
          </button>
        </div>

        <div className="panel-content">
          {user.jobs && user.jobs.length > 0 ? (
            <div className="career-timeline">
              <h3>Career Timeline</h3>
              <div className="timeline">
                {user.jobs.slice().reverse().map((job, index) => (
                  <div key={index} className="timeline-item">
                    <div className="timeline-marker"></div>
                    <div className="timeline-content">
                      <div className="job-header">
                        <h4 className="job-title">{job.title}</h4>
                        <div className="job-company">{job.comp}</div>
                      </div>
                      
                      <div className="job-details">
                        <div className="job-period">
                          {formatYear(job.start_year)} - {formatYear(job.end_year)}
                          {getJobDuration(job) && (
                            <span className="duration"> • {getJobDuration(job)}</span>
                          )}
                        </div>
                        
                        {job.loc && <div className="job-location">📍 {job.loc}</div>}
                        
                        <div className="job-meta">
                          {job.sector && (
                            <span className="meta-tag sector">{job.sector}</span>
                          )}
                          {job.seniority && (
                            <span className="meta-tag seniority">{job.seniority}</span>
                          )}
                          {job.company_size && (
                            <span className="meta-tag company-size">{job.company_size}</span>
                          )}
                          {job.remote_type && (
                            <span className="meta-tag remote">{job.remote_type}</span>
                          )}
                          {job.founder_flag && (
                            <span className="meta-tag founder">Founder</span>
                          )}
                        </div>

                        {job.skill_tags && job.skill_tags.length > 0 && (
                          <div className="skills">
                            <strong>Skills:</strong>
                            <div className="skill-tags">
                              {job.skill_tags.map((skill, skillIndex) => (
                                <span key={skillIndex} className="skill-tag">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="no-career-data">
              <p>No career information available for this alumni.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserDetailsPanel;
