import { useEffect, useState } from 'react';
import { httpService } from '../http/httpService';

function useAutocomplete(search) {
    const [searchResults, setSearchResults] = useState([]);

    const clear = () => setSearchResults([]);

    useEffect(() => {
        httpService.getSearchAddress(search).then(setSearchResults);
    }, [search]);

    return { data: searchResults, clear };
}

export default useAutocomplete;
