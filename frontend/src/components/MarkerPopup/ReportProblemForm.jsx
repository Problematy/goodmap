import axios from 'axios';
import React, { useState } from 'react';
import styled from 'styled-components';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';

const Form = styled.form`
    display: flex;
    flex-direction: column;
    gap: 10px;
`;

const Label = styled.label`
    display: flex;
    flex-direction: column;
    font-size: 1rem;
`;

const Select = styled.select`
    padding: 5px;
    font-size: 1rem;
`;

const Input = styled.input`
    padding: 5px;
    font-size: 1rem;
`;

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
                    <option value={t('reportNotHere')}>{t('reportNotHere')}</option>
                    <option value={t('reportOverload')}>{t('reportOverload')}</option>
                    <option value={t('reportBroken')}>{t('reportBroken')}</option>
                    <option value={t('reportOther')}>{t('reportOther')}</option>
                </Select>
            </Label>
            {problemType === 'other' && (
                <Label>
                    Please describe:
                    <Input
                        type="text"
                        name="problem"
                        value={problem}
                        onChange={e => setProblem(e.target.value)}
                    />
                </Label>
            )}
            {problemType !== `` && <SubmitButton type="submit" value={t('submitProblem')} />}
        </Form>
    );
};

ReportProblemForm.propTypes = {
    placeId: PropTypes.string.isRequired,
};
