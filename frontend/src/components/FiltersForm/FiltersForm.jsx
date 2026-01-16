import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useCategories } from '../Categories/CategoriesContext';
import { httpService } from '../../services/http/httpService';
import FiltersTooltip from './FiltersTooltip';

const FilterSection = styled.div`
    margin-bottom: 20px;

    &:last-child {
        margin-bottom: 0;
    }
`;

const FilterHeader = styled.div`
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
`;

const FilterTitle = styled.span`
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
    line-height: 16px;
`;

const FilterOption = styled.label`
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.2s ease;
    font-size: 14px;

    &:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
`;

const StyledCheckbox = styled.input`
    appearance: none;
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255, 255, 255, 0.5);
    border-radius: 4px;
    background-color: transparent;
    cursor: pointer;
    position: relative;
    flex-shrink: 0;
    transition: all 0.2s ease;

    &:checked {
        background-color: #4fc3f7;
        border-color: #4fc3f7;
    }

    &:checked::after {
        content: '';
        position: absolute;
        left: 5px;
        top: 2px;
        width: 5px;
        height: 9px;
        border: solid white;
        border-width: 0 2px 2px 0;
        transform: rotate(45deg);
    }

    &:focus {
        outline: none;
        box-shadow: 0 0 0 2px rgba(79, 195, 247, 0.4);
    }
`;

const OptionText = styled.span`
    flex: 1;
`;

const TooltipWrapper = styled.span`
    display: flex;
    align-items: center;
    margin-left: auto;
`;

/**
 * Filters form component that allows users to filter map locations by categories.
 * Fetches category data from the API and renders checkboxes for each filter option.
 * Manages filter state through the Categories context.
 *
 * @returns {React.ReactElement} Form element containing categorized filter checkboxes with optional tooltips
 */
export const FiltersForm = () => {
    const { setCategories } = useCategories();
    const [categoriesData, setCategoriesData] = useState([]);

    const handleCheckboxChange = event => {
        const { value, checked } = event.target;
        const category = event.target.dataset.category;

        setCategories(prevSelectedFilters => {
            const newSelectedFilters = { ...prevSelectedFilters };

            if (checked) {
                if (newSelectedFilters[category]) {
                    newSelectedFilters[category].push(value);
                } else {
                    newSelectedFilters[category] = [value];
                }
            } else {
                newSelectedFilters[category] = newSelectedFilters[category].filter(
                    filter => filter !== value,
                );
            }

            return newSelectedFilters;
        });
    };

    useEffect(() => {
        const fetchCategories = async () => {
            const categoriesData = await httpService.getCategoriesData();
            setCategoriesData(categoriesData);
        };
        fetchCategories();
    }, []);

    const renderFilterOptions = (filters, category) => {
        return filters[1].map(([name, translation]) => {
            const tooltipData = globalThis.FEATURE_FLAGS?.CATEGORIES_HELP
                ? filters[3].find(it => it[name])
                : '';
            return (
                <FilterOption key={`${category}-${name}`} htmlFor={name}>
                    <StyledCheckbox
                        onChange={handleCheckboxChange}
                        data-category={category}
                        type="checkbox"
                        id={name}
                        value={name}
                    />
                    <OptionText>{translation}</OptionText>
                    {tooltipData && (
                        <TooltipWrapper>
                            <FiltersTooltip text={tooltipData[name]} />
                        </TooltipWrapper>
                    )}
                </FilterOption>
            );
        });
    };

    const sections = categoriesData.map(filtersData => {
        const [categoryKey, categoryName] = filtersData[0];
        const sectionKey = `${categoryKey}-${categoryName}`;
        const categoryTooltip = globalThis.FEATURE_FLAGS?.CATEGORIES_HELP
            ? filtersData[2].find(it => it[categoryKey])
            : null;

        return (
            <FilterSection key={sectionKey} aria-labelledby={`filter-label-${sectionKey}`}>
                <FilterHeader>
                    <FilterTitle id={`filter-label-${sectionKey}`}>{categoryName}</FilterTitle>
                    {categoryTooltip && <FiltersTooltip text={categoryTooltip[categoryKey]} />}
                </FilterHeader>
                {renderFilterOptions(filtersData, categoryKey)}
            </FilterSection>
        );
    });

    return <form>{sections}</form>;
};
