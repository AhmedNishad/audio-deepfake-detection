'use client'
import React, { useState } from 'react';
import { DetectionResult } from '../types';

const SearchPage = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);

    const handleSearch = async () => {
        try {
            const response = await fetch(`YOUR_API_ENDPOINT?q=${searchQuery}`);
            if (!response.ok) {
                throw new Error('Failed to fetch search results');
            }
            const data = await response.json();
            setSearchResults(data.results);
        } catch (error) {
            console.error('Error fetching search results:', error);
        }
    };

    return (
        <div>
            <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter your search query"
            />
            <button onClick={handleSearch}>Search</button>

            <div>
                {searchResults.map((result: DetectionResult) => (
                    <div key={result._id}>
                        <h3>{result.publicFigure}</h3>
                        <p>{result.transcript}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SearchPage;