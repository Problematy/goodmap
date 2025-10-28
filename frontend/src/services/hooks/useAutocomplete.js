import { useEffect, useState } from 'react';
import { httpService } from '../http/httpService';

/**
 * Custom hook for address autocomplete functionality.
 * Fetches address search results from OpenStreetMap Nominatim API when search query changes.
 *
 * @param {string} search - Search query string
 * @returns {Object} Object containing search results and clear function
 * @returns {Array} returns.data - Array of search result objects
 * @returns {Function} returns.clear - Function to clear search results
 */
function useAutocomplete(search) {
    const [searchResults, setSearchResults] = useState([]);

    const clear = () => setSearchResults([]);

    useEffect(() => {
        httpService.getSearchAddress(search).then(setSearchResults);
    }, [search]);

    return { data: searchResults, clear };
}

export default useAutocomplete;
