import React from 'react';
import styled, { keyframes } from 'styled-components';
import { useTranslation } from 'react-i18next';
import { Tooltip } from '@mui/material';
import { useDeploymentData } from '../../context/DeploymentDataContext';
import { useFilters } from '../../context/FiltersContext';
import FiltersTooltip from './FiltersTooltip';

const shimmer = keyframes`
    0% {
        background-position: -200px 0;
    }
    100% {
        background-position: 200px 0;
    }
`;

const SkeletonBox = styled.div`
    background: linear-gradient(
        90deg,
        rgba(255, 255, 255, 0.1) 25%,
        rgba(255, 255, 255, 0.2) 50%,
        rgba(255, 255, 255, 0.1) 75%
    );
    background-size: 200px 100%;
    animation: ${shimmer} 1.5s infinite;
    border-radius: 4px;
`;

const SkeletonTitle = styled(SkeletonBox)`
    height: 16px;
    width: 120px;
    margin-bottom: 12px;
`;

const SkeletonOption = styled(SkeletonBox)`
    height: 34px;
    width: 100%;
    margin: 4px 0;
    border-radius: 8px;
`;

const SkeletonSection = styled.div`
    margin-bottom: 20px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);

    &:last-child {
        margin-bottom: 0;
        border-bottom: none;
    }
`;

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
    flex: 1;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.3px;
    line-height: 16px;
`;

// Every filter mode gets a small badge next to its category title, so "or"
// and "and" (both checkboxes, otherwise visually identical at rest) are as
// distinguishable as "exclusive"/"threshold" already are via their radio
// shape. Kept to a single subtle character rather than a word, with the
// full explanation one hover/focus away in the tooltip.
const MODE_BADGES = {
    or: { badge: 'filterModeOrBadge', tooltip: 'filterModeOrTooltip' },
    and: { badge: 'filterModeAndBadge', tooltip: 'filterModeAndTooltip' },
    exclusive: { badge: 'filterModeExclusiveBadge', tooltip: 'filterModeExclusiveTooltip' },
    boolean: { badge: 'filterModeBooleanBadge', tooltip: 'filterModeBooleanTooltip' },
    threshold: { badge: 'filterModeThresholdBadge', tooltip: 'filterModeThresholdTooltip' },
};

const ModeBadge = styled.span`
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 15px;
    height: 15px;
    padding: 0 3px;
    border-radius: 50%;
    font-size: 10px;
    font-weight: 700;
    line-height: 1;
    background-color: rgba(79, 195, 247, 0.18);
    color: #4fc3f7;
    border: 1px solid rgba(79, 195, 247, 0.45);
    cursor: help;
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

    &[type='radio'] {
        border-radius: 50%;
    }

    &[type='radio']:checked::after {
        left: 4px;
        top: 4px;
        width: 6px;
        height: 6px;
        border: none;
        border-radius: 50%;
        background-color: white;
        transform: none;
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

const ErrorMessage = styled.p`
    font-size: 14px;
    margin-bottom: 12px;
`;

const RetryButton = styled.button`
    font-size: 14px;
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    background: transparent;
    color: inherit;
    cursor: pointer;

    &:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
`;

const ClearFiltersButton = styled.button`
    font-size: 14px;
    padding: 8px 12px;
    margin-top: 8px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.5);
    background: transparent;
    color: inherit;
    cursor: pointer;
    width: 100%;

    &:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
`;

/**
 * Filters form component that allows users to filter map locations by categories.
 * Fetches category data from the API and renders checkboxes for each filter option.
 * Manages filter state through the Categories context.
 *
 * @return {React.ReactElement} Form element containing categorized filter checkboxes with optional tooltips
 */
const LoadingSkeleton = () => (
    <>
        <SkeletonSection>
            <SkeletonTitle />
            <SkeletonOption />
            <SkeletonOption />
            <SkeletonOption />
        </SkeletonSection>
        <SkeletonSection>
            <SkeletonTitle />
            <SkeletonOption />
            <SkeletonOption />
        </SkeletonSection>
    </>
);

const FiltersForm = () => {
    const { t } = useTranslation();
    const { categoriesData, categoriesLoading, categoriesError, refetchCategories } =
        useDeploymentData();
    const { selectedFilters, setSelectedFilters } = useFilters();

    const handleCheckboxChange = event => {
        const { value, checked } = event.target;
        const { category } = event.target.dataset;

        setSelectedFilters(prevSelectedFilters => {
            const newSelectedFilters = { ...prevSelectedFilters };

            if (checked) {
                newSelectedFilters[category] = [...(newSelectedFilters[category] ?? []), value];
            } else {
                newSelectedFilters[category] = newSelectedFilters[category].filter(
                    filter => filter !== value,
                );
            }

            return newSelectedFilters;
        });
    };

    // "exclusive" categories are single-select (radio buttons): picking one
    // option replaces any previous selection instead of toggling it.
    const handleRadioChange = event => {
        const { value } = event.target;
        const { category } = event.target.dataset;

        setSelectedFilters(prevSelectedFilters => ({
            ...prevSelectedFilters,
            [category]: [value],
        }));
    };

    const handleClearFilters = () => {
        setSelectedFilters({});
    };

    const renderModeBadge = mode => {
        const keys = MODE_BADGES[mode] ?? MODE_BADGES.or;
        const tooltipText = t(keys.tooltip);
        return (
            <Tooltip
                title={tooltipText}
                placement="top"
                arrow
                enterTouchDelay={0}
                leaveTouchDelay={3000}
            >
                <ModeBadge
                    tabIndex={0}
                    aria-label={t('filterModeHelpAriaLabel', { description: tooltipText })}
                >
                    {t(keys.badge)}
                </ModeBadge>
            </Tooltip>
        );
    };

    const renderFilterOptions = category => {
        // "exclusive" (pick one) and "threshold" (pick a cumulative upper bound,
        // e.g. speed limit) are both single-select: rendered as radio buttons so
        // only one option can be active at a time.
        //
        // TODO: "threshold" categories would read more naturally as an MUI
        // <Slider> with discrete `marks` at each option value - the filled
        // track from min to the thumb is a direct visual match for "everything
        // up to here is included," better than a radio group. Needs a design
        // decision first: sliders have no natural "nothing selected" state (the
        // thumb always sits somewhere), but "no filter" must stay distinct from
        // "lowest value selected" - e.g. an explicit "Any" mark left of the
        // lowest real value, or relying on the existing "Clear filters" button
        // as the only way back to unset. Also needs keyboard/screen-reader
        // slider accessibility and updated frontend/e2e tests.
        const { categoryKey, options, optionsHelp, filterMode } = category;
        const isSingleSelect = filterMode === 'exclusive' || filterMode === 'threshold';
        return options.map(([name, translation]) => {
            const tooltipData = globalThis.FEATURE_FLAGS?.CATEGORIES_HELP
                ? optionsHelp.find(it => it[name])
                : '';
            return (
                <FilterOption key={`${categoryKey}-${name}`} htmlFor={name}>
                    <StyledCheckbox
                        onChange={isSingleSelect ? handleRadioChange : handleCheckboxChange}
                        data-category={categoryKey}
                        type={isSingleSelect ? 'radio' : 'checkbox'}
                        name={isSingleSelect ? categoryKey : undefined}
                        id={name}
                        value={name}
                        checked={Boolean(selectedFilters[categoryKey]?.includes(name))}
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

    // "boolean" categories (e.g. "free only") have exactly one meaningful filter
    // state - leaving them unchecked already means "show everything" - so rather
    // than giving each its own titled section, they're grouped into one shared
    // "Others" section as plain checkboxes labeled with the category's own name.
    // This keeps the panel compact as more true/false-style filters are added.
    const isBooleanCategory = category => category.filterMode === 'boolean';
    const booleanCategories = categoriesData.filter(isBooleanCategory);
    const otherCategories = categoriesData.filter(f => !isBooleanCategory(f));

    const renderBooleanFilterOption = category => {
        const { categoryKey, categoryName, options, optionsHelp } = category;
        const trueOption = options.find(([optionValue]) => optionValue === 'true');
        if (!trueOption) {
            return null;
        }
        const [name] = trueOption;
        const tooltipData = globalThis.FEATURE_FLAGS?.CATEGORIES_HELP
            ? optionsHelp.find(it => it[name])
            : '';
        return (
            <FilterOption key={categoryKey} htmlFor={categoryKey}>
                <StyledCheckbox
                    onChange={handleCheckboxChange}
                    data-category={categoryKey}
                    type="checkbox"
                    id={categoryKey}
                    value={name}
                    checked={Boolean(selectedFilters[categoryKey]?.includes(name))}
                />
                <OptionText>{categoryName}</OptionText>
                {renderModeBadge('boolean')}
                {tooltipData && (
                    <TooltipWrapper>
                        <FiltersTooltip text={tooltipData[name]} />
                    </TooltipWrapper>
                )}
            </FilterOption>
        );
    };

    const sections = otherCategories.map(category => {
        const { categoryKey, categoryName, categoriesHelp, filterMode } = category;
        // Built from categoryKey alone (not categoryName): aria-labelledby
        // values are parsed as space-separated ID references, so an id built
        // from a category's translated name (e.g. "accessible by") would
        // silently break the association for any name containing whitespace.
        const sectionId = `filter-label-${categoryKey}`;
        const categoryTooltip = globalThis.FEATURE_FLAGS?.CATEGORIES_HELP
            ? categoriesHelp.find(it => it[categoryKey])
            : null;

        return (
            <FilterSection key={categoryKey} aria-labelledby={sectionId}>
                <FilterHeader>
                    <FilterTitle id={sectionId}>{categoryName}</FilterTitle>
                    {renderModeBadge(filterMode)}
                    {categoryTooltip && <FiltersTooltip text={categoryTooltip[categoryKey]} />}
                </FilterHeader>
                {renderFilterOptions(category)}
            </FilterSection>
        );
    });

    if (booleanCategories.length > 0) {
        sections.push(
            <FilterSection key="others-section" aria-labelledby="filter-label-others">
                <FilterHeader>
                    <FilterTitle id="filter-label-others">{t('otherFilters')}</FilterTitle>
                </FilterHeader>
                {booleanCategories.map(renderBooleanFilterOption)}
            </FilterSection>,
        );
    }

    if (categoriesLoading) {
        return (
            <form>
                <LoadingSkeleton />
            </form>
        );
    }

    if (categoriesError) {
        return (
            <form>
                <ErrorMessage>{t('loadFiltersError')}</ErrorMessage>
                <RetryButton type="button" onClick={refetchCategories}>
                    {t('retry')}
                </RetryButton>
            </form>
        );
    }

    return (
        <form>
            {sections}
            <ClearFiltersButton
                id="clear-filters-button"
                type="button"
                aria-label={t('clearAllFiltersAriaLabel')}
                onClick={handleClearFilters}
            >
                {t('clearFilters')}
            </ClearFiltersButton>
        </form>
    );
};

export default FiltersForm;
