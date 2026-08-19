import axios from 'axios';
import React, { useState } from 'react';
import styled from 'styled-components';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import getCsrfToken from '../../utils/csrf';
import { useDeploymentData } from '../../context/DeploymentDataContext';

/**
 * Styled form component with flexbox column layout.
 */
const Form = styled.form`
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 12px 15px;
    background-color: #f8f9fa;
    border-radius: 8px;
    margin: 10px 15px;
`;

/**
 * Styled label component with column layout for form fields.
 */
const Label = styled.label`
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 12px;
    font-weight: 500;
    color: #555;
`;

/**
 * Styled select dropdown component.
 */
const Select = styled.select`
    padding: 10px 12px;
    font-size: 13px;
    border: 1px solid #ddd;
    border-radius: 6px;
    background-color: white;
    cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s;

    &:hover {
        border-color: #aaa;
    }

    &:focus {
        outline: none;
        border-color: #007bff;
        box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.15);
    }
`;

/**
 * Styled text input component.
 */
const Input = styled.input`
    padding: 10px 12px;
    font-size: 13px;
    border: 1px solid #ddd;
    border-radius: 6px;
    transition: border-color 0.2s, box-shadow 0.2s;

    &:hover {
        border-color: #aaa;
    }

    &:focus {
        outline: none;
        border-color: #007bff;
        box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.15);
    }
`;

/**
 * Styled submit button component with hover effect.
 */
const SubmitButton = styled.input`
    padding: 10px 16px;
    background-color: #d32f2f;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: background-color 0.2s, transform 0.1s;

    &:hover {
        background-color: #b71c1c;
    }

    &:active {
        transform: scale(0.98);
    }
`;

/**
 * Styled success message component.
 */
const ErrorMessage = styled.div`
    padding: 12px 15px;
    background-color: #fdecea;
    border: 1px solid #f5c6cb;
    border-radius: 8px;
    color: #b71c1c;
    font-size: 13px;
    margin: 10px 15px;
    text-align: center;
`;

const RetryButton = styled.button`
    margin-top: 8px;
    font-size: 13px;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid currentColor;
    background: transparent;
    color: inherit;
    cursor: pointer;
`;

const SuccessMessage = styled.div`
    padding: 12px 15px;
    background-color: #e8f5e9;
    border: 1px solid #a5d6a7;
    border-radius: 8px;
    color: #2e7d32;
    font-size: 13px;
    margin: 10px 15px;
    text-align: center;
`;

/**
 * Form component for reporting problems with a location.
 * Allows users to select from predefined problem types or describe a custom issue.
 * Fetches CSRF token and submits the report to the API.
 * Shows a success message after submission.
 *
 * @param {Object} props - Component props
 * @param {string} props.placeId - UUID of the location being reported
 * @returns {React.ReactElement} Form for reporting problems or success message after submission
 */
/**
 * Get issue type options from backend configuration or fall back to defaults.
 * Dynamic types come from the deployment's location schema (reported_issue_types).
 * Default types are kept for backward compatibility with backends that don't provide this field (until 2.0.0).
 *
 * @param {Function} t - Translation function
 * @param {Array<{value: string, label: string}>} [dynamicTypes] - Types this deployment declares
 * @returns {Array<{value: string, label: string}>} Issue type options (without "other", which is always appended)
 */
const getIssueTypeOptions = (t, dynamicTypes) => {
    if (dynamicTypes && dynamicTypes.length > 0) {
        return dynamicTypes.map(type => ({
            value: type.value,
            label: type.label,
        }));
    }
    // Backward-compatible defaults (remove in 2.0.0)
    return [
        { value: 'notHere', label: t('reportNotHere') },
        { value: 'overload', label: t('reportOverload') },
        { value: 'broken', label: t('reportBroken') },
    ];
};

const ReportProblemForm = ({ placeId }) => {
    const { t } = useTranslation();
    const { locationSchema, schemaError, refetchLocationSchema } = useDeploymentData();
    const [problem, setProblem] = useState('');
    const [problemType, setProblemType] = useState('');
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [responseMessage, setResponseMessage] = useState('');

    // Only reached once the schema is known, so a loaded schema declaring no issue
    // types is the one case that falls back to the legacy defaults.
    const issueTypeOptions = getIssueTypeOptions(t, locationSchema?.reported_issue_types);

    const handleSubmit = async event => {
        event.preventDefault();
        const csrfToken = await getCsrfToken();

        const response = await axios.post(
            '/api/report-location',
            {
                id: placeId,
                description: problemType === 'other' ? problem : problemType,
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
            },
        );
        const responseData = response.data;
        setResponseMessage(responseData.message);
        setIsSubmitted(true);
    };

    if (isSubmitted) {
        return <SuccessMessage>{responseMessage}</SuccessMessage>;
    }

    // This deployment's own issue types are the only ones it is guaranteed to accept, so
    // the form is withheld until they are known: the legacy fallbacks are not a stand-in
    // for them. A failed fetch has to say so, or the form would just never appear.
    if (schemaError) {
        return (
            <ErrorMessage>
                <span role="alert">{t('loadReportFormError')}</span>
                <div>
                    <RetryButton type="button" onClick={refetchLocationSchema}>
                        {t('retry')}
                    </RetryButton>
                </div>
            </ErrorMessage>
        );
    }

    if (!locationSchema) {
        return null;
    }

    return (
        <Form onSubmit={handleSubmit}>
            <Label>
                {t('reportProblemLabel')}
                <Select value={problemType} onChange={e => setProblemType(e.target.value)}>
                    <option value="">{t('reportChooseOption')}</option>
                    {issueTypeOptions.map(opt => (
                        <option key={opt.value} value={opt.value}>
                            {opt.label}
                        </option>
                    ))}
                    <option value="other">{t('reportOther')}</option>
                </Select>
            </Label>
            {problemType === 'other' && (
                <Label>
                    {t('describeOtherProblem')}:
                    <Input
                        type="text"
                        name="problem"
                        value={problem}
                        onChange={e => setProblem(e.target.value)}
                    />
                </Label>
            )}
            {problemType !== '' && <SubmitButton type="submit" value={t('submitProblem')} />}
        </Form>
    );
};

ReportProblemForm.propTypes = {
    placeId: PropTypes.string.isRequired,
};

export default ReportProblemForm;
