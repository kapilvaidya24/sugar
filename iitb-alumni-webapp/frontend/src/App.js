import React, { useState, useEffect } from 'react';
import './App.css';
import SearchBar from './components/SearchBar';
import AlumniGrid from './components/AlumniGrid';
import UserDetailsPanel from './components/UserDetailsPanel';

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [allAlumni, setAllAlumni] = useState([]);
  const [filteredAlumni, setFilteredAlumni] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [selectedUser, setSelectedUser] = useState(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  // Load all data once on startup
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load alumni data from static JSON file
        const response = await fetch('/data.json');
        const alumniData = await response.json();

        // Filter out alumni with no job information and process data
        const processedAlumni = Object.values(alumniData)
          .filter(person => person.jobs && person.jobs.length > 0)
          .map(person => ({
            ...person,
            firstJob: person.jobs[0]
          }));

                // Calculate basic stats
        const companies = new Set();
        const locations = new Set();
        const graduationYears = new Set();
        
        processedAlumni.forEach(person => {
          if (person.grad_yr) graduationYears.add(person.grad_yr);
          if (person.firstJob?.comp) companies.add(person.firstJob.comp);
          if (person.firstJob?.loc) locations.add(person.firstJob.loc);
        });
        
        const calculatedStats = {
          total_alumni: processedAlumni.length,
          unique_companies: companies.size,
          unique_locations: locations.size,
        };

        setAllAlumni(processedAlumni);
        setFilteredAlumni(processedAlumni);
        setStats(calculatedStats);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

    // Simple search functionality (ag-Grid will handle advanced filtering)
  useEffect(() => {
    let results = allAlumni;
    
    if (searchQuery.trim()) {
      const queryLower = searchQuery.toLowerCase();
      results = allAlumni.filter(person => {
        return (
          (person.name && person.name.toLowerCase().includes(queryLower)) ||
          (person.firstJob?.comp && person.firstJob.comp.toLowerCase().includes(queryLower)) ||
          (person.firstJob?.title && person.firstJob.title.toLowerCase().includes(queryLower)) ||
          (person.firstJob?.loc && person.firstJob.loc.toLowerCase().includes(queryLower))
        );
      });
    }
    
    setFilteredAlumni(results);
  }, [allAlumni, searchQuery]);

  const handleSearch = (query) => {
    setSearchQuery(query);
  };

  const handleRowClick = (user) => {
    setSelectedUser(user);
    setIsPanelOpen(true);
  };

  const handlePanelClose = () => {
    setIsPanelOpen(false);
    setSelectedUser(null);
  };

  return (
    <div className="App">
      {loading ? (
        <div className="loading-screen">
          <div className="loading-content">
            <div className="loading-spinner"></div>
            <h2>Loading Alumni Database</h2>
            <p>Preparing {allAlumni.length > 0 ? `${allAlumni.length} ` : ''}alumni profiles...</p>
          </div>
        </div>
      ) : (
        <>
          <header className="App-header">
            <h1>explore alumni from IITB CSE</h1>
            <div className="stats-bar">
              {stats && `${stats.total_alumni} alumni • ${filteredAlumni.length} showing`}
            </div>
          </header>

                    <main className={`App-main ${isPanelOpen ? 'panel-open' : ''}`}>
            <div className="controls-section">
              <SearchBar onSearch={handleSearch} />
            </div>
            
            <AlumniGrid 
              alumni={filteredAlumni} 
              onRowClick={handleRowClick}
            />
            
            <UserDetailsPanel
              user={selectedUser}
              isOpen={isPanelOpen}
              onClose={handlePanelClose}
            />
          </main>
        </>
      )}
    </div>
  );
}

export default App;
