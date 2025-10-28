import axios from 'axios';
import React, { useState } from 'react';
import styled from 'styled-components';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';

/**
 * Styled form component with flexbox column layout.
 */
const Form = styled.form`
    display: flex;
    flex-direction: column;
    gap: 10px;
`;

/**
 * Styled label component with column layout for form fields.
 */
const Label = styled.label`
    display: flex;
    flex-direction: column;
    font-size: 1rem;
`;

/**
 * Styled select dropdown component.
 */
const Select = styled.select`
    padding: 5px;
    font-size: 1rem;
`;

/**
 * Styled text input component.
 */
const Input = styled.input`
    padding: 5px;
    font-size: 1rem;
`;

/**
 * Styled submit button component with hover effect.
 */
const SubmitButton = styled.input`
    padding: 10px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1rem;

    &:hover {
        background-color: #0056b3;
    }
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
export const ReportProblemForm = ({ placeId }) => {
    const { t } = useTranslation();
    const [problem, setProblem] = useState('');
    const [problemType, setProblemType] = useState('');
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [responseMessage, setResponseMessage] = useState('');

    const fetchCsrfToken = async () => {
        const response = await axios.get('/api/generate-csrf-token');
        return response.data.csrf_token;
    };

    const handleSubmit = async event => {
        event.preventDefault();
        const csrfToken = await fetchCsrfToken();

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
        return <p>{responseMessage}</p>;
    }

    return (
        <Form onSubmit={handleSubmit}>
            <Label>
                Problem:
                <Select value={problemType} onChange={e => setProblemType(e.target.value)}>
                    <option value="">--{t('reportChooseOption')}--</option>
                    <option value="notHere">{t('reportNotHere')}</option>
                    <option value="overload">{t('reportOverload')}</option>
                    <option value="broken">{t('reportBroken')}</option>
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
