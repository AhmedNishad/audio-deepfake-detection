'use client'
import React, { useEffect, useState } from 'react';
import { DetectionResult } from '../types';
import { apiUrl } from '@/conts';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { capitalizeEachWord } from '../page';

const SearchPage = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<DetectionResult[]>([]);
    const searchParams = useSearchParams()
    const searchText = searchParams.get('text');
    const [celebrities, setCelebrities] = useState([]);

    useEffect(() => {
        if (searchQuery && searchQuery !== "") {
            (async () => {
                const response = await fetch(`https://api.api-ninjas.com/v1/celebrity?name=${searchQuery}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Api-Key': 'ZzzuCKOo/zf/F3GMXgXz1w==UNVkljCUHfJ48ZdU'
                    },
                });
                const data = await response.json();
                console.log(data);
                const celebrityNames = data.sort((d: any) => d.net_worth).slice(0, 5).map((d: any) => capitalizeEachWord(d.name))
                console.log(celebrityNames);
                setCelebrities(celebrityNames);
            })();
        }
    }, [searchQuery])

    const searchRequest = async (text?: string) => {
        try {
            const response = await fetch(`${apiUrl}/search?text=${text ?? searchQuery}`);
            if (!response.ok) {
                throw new Error('Failed to fetch search results');
            }
            const data = await response.json();
            console.log(data)
            setSearchResults(data);
        } catch (error) {
            console.error('Error fetching search results:', error);
        }
    }

    const handleSearch = async () => {
        await searchRequest();
    };

    useEffect(() => {
        (async () => {
            if (searchText) {
                console.log("Setting search term", searchText)
                setSearchQuery(searchText);
                await searchRequest(searchText)
            }
        })();
    }, [searchText])

    return (
        <div className="container">
            <div className="search-container relative">
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Enter your search query"
                    className="border border-gray-300 rounded-md py-2 px-4 mb-4"
                />
                {celebrities.length > 0 && (
                    <ul style={{ top: '40px' }} className="absolute left-0 z-10 bg-white border border-gray-300 rounded-b-md shadow-md mt-2 w-full">
                        {celebrities.map((celebrity, index) => (
                            <li
                                key={index}
                                onClick={() => { setSearchQuery(celebrity); setCelebrities([]) }}
                                className="py-2 px-4 cursor-pointer hover:bg-gray-100"
                            >
                                {celebrity}
                            </li>
                        ))}
                    </ul>
                )}
                <button onClick={handleSearch} className="bg-black text-white py-2 px-4 ml-4 rounded-md">Search</button>
            </div>
            <div>
                {searchResults && (
                    <>
                        <p className="mb-2">Search returned {searchResults.length} result(s)</p>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {searchResults.map((result: DetectionResult) => (
                                <div key={result._id.$oid} className="border border-gray-300 rounded-md p-4">
                                    <h3 className="text-xl font-semibold mb-2">{result.publicFigure}</h3>
                                    <p className="mb-2 overflow-hidden line-clamp-2">{result.transcript}</p>
                                    <Link className="text-blue-500 hover:underline" href={`detail?id=${result._id.$oid}`}>
                                        View
                                    </Link>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </div>

    );
};

export default SearchPage;