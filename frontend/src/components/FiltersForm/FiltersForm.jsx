import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useCategories } from '../Categories/CategoriesContext';
import useDebounce from '../../utils/hooks/useDebounce';
import { httpService } from '../../services/http/httpService';
import { useMapStore } from '../Map/store/map.store';
import FiltersTooltip from './FiltersTooltip';

/**
 * Filters form component that allows users to filter map locations by categories.
 * Fetches category data from the API and renders checkboxes for each filter option.
 * Manages filter state through the Categories context and debounces map configuration updates.
 *
 * @returns {React.ReactElement} Form element containing categorized filter checkboxes with optional tooltips
 */
export const FiltersForm = () => {
    const { setCategories } = useCategories();
    const [categoriesData, setCategoriesData] = useState([]);
    const mapConfiguration = useMapStore(state => state.mapConfiguration);
    const mapConfigDebounced = useDebounce(mapConfiguration, 5000);

    useEffect(() => {
        if (mapConfigDebounced === null) {
            return;
        }
    }, [mapConfigDebounced]);

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
                <div className="form-check" key={`${category}-${name}`}>
                    <label htmlFor={name}>
                        {translation}
                        <input
                            onChange={handleCheckboxChange}
                            className="form-check-input filter"
                            data-category={category}
                            type="checkbox"
                            id={name}
                            value={name}
                        />
                        {tooltipData && <FiltersTooltip text={tooltipData[name]} />}
                    </label>
                </div>
            );
        });
    };

    const sections = categoriesData.map(filtersData => (
        <div
            key={`${filtersData[0][0]}-${filtersData[0][1]}`}
            aria-labelledby={`filter-label-${filtersData[0][0]}-${filtersData[0][1]}`}
        >
            <span id={`filter-label-${filtersData[0][0]}-${filtersData[0][1]}`}>
                {filtersData[0][1]}
            </span>
            {globalThis.FEATURE_FLAGS?.CATEGORIES_HELP &&
                filtersData[2].find(it => it[filtersData[0][0]]) && (
                    <FiltersTooltip
                        text={filtersData[2].find(it => it[filtersData[0][0]])[filtersData[0][0]]}
                    />
                )}
            {renderFilterOptions(filtersData, filtersData[0][0])}
        </div>
    ));

    return <form>{sections}</form>;
};
