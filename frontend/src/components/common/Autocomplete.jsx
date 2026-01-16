import React, { useState, useEffect, useCallback, useRef } from 'react';
import styled from 'styled-components';
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
    const timeoutRef = useRef(null);

    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    const handleInputChange = e => {
        const term = e.target.value;
        setSearchTerm(term);
    };

    const clickItem = useCallback(
        item => {
            setSearchTerm(item.display_name);
            onClick(item);
            timeoutRef.current = setTimeout(() => {
                clear();
            }, 400);
        },
        [onClick, clear],
    );

    const primaryColor = globalThis.PRIMARY_COLOR || 'white';
    const secondaryColor = globalThis.SECONDARY_COLOR || 'black';

    return (
        <Box style={{ backgroundColor: primaryColor }}>
            <InputBox>
                <StyledInput
                    type="text"
                    value={searchTerm}
                    onChange={handleInputChange}
                    placeholder={t('search')}
                    $primaryColor={primaryColor}
                    $secondaryColor={secondaryColor}
                    style={{
                        backgroundColor: primaryColor,
                        borderColor: secondaryColor,
                        color: secondaryColor,
                    }}
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
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
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
    border: 2px solid;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;

    &::placeholder {
        color: ${props => props.$secondaryColor || 'black'};
        opacity: 0.7;
        font-weight: 500;
    }

    &:focus {
        box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.3);
    }
`;

const SuggestionList = styled.ul`
    z-index: 9999999;
    position: absolute;
    top: 54px;
    min-width: 100%;
    max-width: 100%;
    border-radius: 8px;
    background-color: white;
    padding: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    margin: 0;
`;

const SuggestionItem = styled.li`
    max-width: 100%;
    cursor: pointer;
    font-size: 0.875rem;
    list-style-type: none;
    padding: 10px 12px;
    border-radius: 6px;
    transition: background-color 0.15s ease;

    &:hover {
        background-color: rgba(0, 102, 204, 0.1);
    }
`;

export default AutoComplete;
