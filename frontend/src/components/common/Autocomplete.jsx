import React, { useState, useEffect, useCallback } from 'react';
import styled, { css } from 'styled-components';
import { useTranslation } from 'react-i18next';
import PropTypes from 'prop-types';
import useDebounce from '../../utils/hooks/useDebounce';
import useAutocomplete from '../../services/hooks/useAutocomplete';

/**
 * Autocomplete search component with debounced input and suggestion dropdown.
 * Provides search functionality with real-time suggestions from an autocomplete service.
 *
 * @param {Object} props - Component props
 * @param {Function} props.onClick - Callback function triggered when a suggestion is clicked
 * @returns {React.ReactElement} Autocomplete input with suggestion dropdown
 */
const AutoComplete = ({ onClick }) => {
    const [searchTerm, setSearchTerm] = useState('');
    const searchTermDebounced = useDebounce(searchTerm);
    const { data, clear } = useAutocomplete(searchTermDebounced);
    const { t } = useTranslation();

    const handleInputChange = e => {
        const term = e.target.value;
        setSearchTerm(term);
    };

    const clickItem = useCallback(item => {
        setSearchTerm(item.display_name);
        onClick(item);
        setTimeout(() => {
            clear();
        }, 400);
    }, []);

    return (
        <Box>
            <InputBox>
                <StyledInput
                    type="text"
                    value={searchTerm}
                    onChange={handleInputChange}
                    placeholder={t('search')}
                />
            </InputBox>

            {data.some(it => it.display_name !== searchTerm) && (
                <SuggestionList>
                    {data
                        .filter(it => it.display_name !== searchTerm)
                        .map(item => (
                            <SuggestionItem key={item?.place_id} onClick={() => clickItem(item)}>
                                {item.display_name}
                            </SuggestionItem>
                        ))}
                </SuggestionList>
            )}
        </Box>
    );
};

AutoComplete.propTypes = {
    onClick: PropTypes.func.isRequired,
};

const Box = styled.div`
    z-index: 999999999;
    background-color: ${globalThis.SECONDARY_COLOR || '#0066CC'};
    border-radius: 5px;
`;

const InputBox = styled.div`
    height: 50px;
`;

const StyledInput = styled.input`
    margin: 0 auto;
    height: 100%;
    width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: center;
    outline: none;
    background-color: ${globalThis.SECONDARY_COLOR || '#0066CC'};
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 1rem;
`;

const SuggestionList = styled.ul`
    z-index: 9999999;
    position: absolute;
    top: 50px;
    min-width: 100%;
    max-width: 100%;
    border-radius: 0.5rem;
    background-color: white;
    padding: 0.25rem;
`;

const SuggestionItem = styled.li`
    max-width: 100%;
    cursor: pointer;
    font-size: 0.875rem;
    list-style-type: none;
`;

export default AutoComplete;
