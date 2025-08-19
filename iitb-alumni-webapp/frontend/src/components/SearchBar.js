import React, { useState, useEffect } from 'react';
import './SearchBar.css';

const SearchBar = ({ onSearch }) => {
    const [query, setQuery] = useState('');

    // Real-time search with debouncing
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            onSearch(query);
        }, 300);

        return () => clearTimeout(timeoutId);
    }, [query, onSearch]);

    const handleClear = () => {
        setQuery('');
    };

      return (
    <div className="search-container">
      <div className="search-input-container">
        <div className="search-icon">⌕</div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="search alumni..."
          className="search-input"
        />
        {query && (
          <button 
            type="button" 
            className="clear-button"
            onClick={handleClear}
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};

export default SearchBar;
