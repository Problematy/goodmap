import React, { useState, useEffect } from 'react';
import {
    Button,
    Box,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Select,
    MenuItem,
    InputLabel,
    FormControl,
    IconButton,
    Checkbox,
    ListItemText,
    OutlinedInput,
    Tooltip,
    Alert,
} from '@mui/material';

import AddAPhotoIcon from '@mui/icons-material/AddAPhoto';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import Control from 'react-leaflet-custom-control';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { buttonStyle, getLocationAwareStyles } from '../../../styles/buttonStyle';
import { getCsrfToken } from '../../../utils/csrf';
import { useLocation } from '../context/LocationContext';
import { httpService } from '../../../services/http/httpService';
import { toast } from '../../../utils/toast';
import { compressImageToJpeg } from '../../../utils/imageCompression';

// Map a category's options to a { key: translation } object.
// Options come as [[key, translation], ...] or [key, ...].
const mapCategoryOptions = categoryOptions => {
    const optionMap = {};
    categoryOptions.forEach(opt => {
        if (Array.isArray(opt)) {
            optionMap[opt[0]] = opt[1];
        } else {
            optionMap[opt] = opt;
        }
    });
    return optionMap;
};

// Build { fieldNames, options } translation maps from httpService.getCategoriesData()'s
// { categories: [{ categoryKey, categoryName, options }, ...] } shape.
const buildCategoryTranslations = categoriesData => {
    const fieldNames = {};
    const options = {};

    (categoriesData.categories || []).forEach(
        ({ categoryKey, categoryName, options: categoryOptions }) => {
            fieldNames[categoryKey] = categoryName;

            if (categoryOptions && categoryOptions.length > 0) {
                options[categoryKey] = mapCategoryOptions(categoryOptions);
            }
        },
    );

    return { fieldNames, options };
};

/**
 * Button component that allows users to suggest new map points/locations.
 * Opens a dialog form with dynamically generated fields based on window.LOCATION_SCHEMA.
 * The form includes the user's position, optional photo upload, and fields for all
 * obligatory location attributes defined in the backend schema.
 * Requires user's geolocation permission to function properly.
 *
 * @returns {React.ReactElement} Button with dialog form for suggesting new points
 */
export const SuggestNewPointButton = () => {
    const { t } = useTranslation();
    const { locationGranted, userPosition, requestLocationWithFeedback } = useLocation();
    const [showNewPointBox, setShowNewPointSuggestionBox] = useState(false);
    const [photo, setPhoto] = useState(null);
    const [photoURL, setPhotoURL] = useState(null);
    // Rendered inline in the dialog rather than as a toast: this dialog sits inside the
    // map's component tree, where an ancestor (e.g. a Leaflet pane) can trap a toast's
    // z-index in its own stacking context, leaving it hidden behind the dialog itself.
    const [formError, setFormError] = useState(null);
    const [categoryTranslations, setCategoryTranslations] = useState({
        fieldNames: {},
        options: {},
    });

    // Fetch translated category data
    useEffect(() => {
        const fetchCategories = async () => {
            try {
                const categoriesData = await httpService.getCategoriesData();
                setCategoryTranslations(buildCategoryTranslations(categoriesData));
            } catch (error) {
                console.error('Failed to fetch category translations:', error);
            }
        };

        fetchCategories();
    }, []);

    // Read location schema from global object. `photo` mirrors the backend's AttachmentConfig
    // (see goodmap.py) so the frontend never has to guess/duplicate the limits it enforces.
    const locationSchema = globalThis.LOCATION_SCHEMA || {
        obligatory_fields: [],
        categories: {},
    };
    const {
        allowed_extensions: allowedPhotoExtensions = [],
        allowed_mime_types: allowedPhotoMimeTypes = [],
        max_size_bytes: maxPhotoSizeBytes = 0,
    } = locationSchema.photo || {};
    const photoInputAccept = [
        ...allowedPhotoMimeTypes,
        ...allowedPhotoExtensions.map(ext => `.${ext}`),
    ].join(',');

    // Initialize dynamic form fields based on schema
    const initializeFormFields = () => {
        const fields = {};
        locationSchema.obligatory_fields.forEach(([fieldName, fieldType]) => {
            // Skip uuid - it's generated on backend
            if (fieldName === 'uuid') {
                return;
            }
            if (fieldType === 'list') {
                fields[fieldName] = [];
            } else {
                fields[fieldName] = '';
            }
        });
        return fields;
    };

    const [formFields, setFormFields] = useState(initializeFormFields);

    const handleNewPointButton = () => {
        requestLocationWithFeedback(() => {
            setFormError(null);
            setShowNewPointSuggestionBox(true);
        });
    };

    const handleLocateMe = () => {
        requestLocationWithFeedback();
    };

    const handleCloseNewPointBox = () => {
        setShowNewPointSuggestionBox(false);
    };

    const acceptPhoto = file => {
        setFormError(null);
        setPhoto(file);
        setPhotoURL(URL.createObjectURL(file));
    };

    const handlePhotoUpload = async event => {
        const file = event.target.files[0];
        if (!file) {
            return;
        }

        if (allowedPhotoMimeTypes.includes(file.type) && file.size <= maxPhotoSizeBytes) {
            acceptPhoto(file);
            return;
        }

        // Anything else (wrong format, oversized, or both) gets normalized to what the
        // backend accepts: oversized photos are usually just high-resolution camera shots
        // rather than genuinely undersizable, and re-encoding also fixes the format.
        try {
            const compressed = await compressImageToJpeg(file, { maxSizeBytes: maxPhotoSizeBytes });
            if (compressed.size > maxPhotoSizeBytes) {
                setFormError(t('fileTooLarge', { maxSizeMB: Math.floor(maxPhotoSizeBytes / 1024 / 1024) }));
                return;
            }
            acceptPhoto(compressed);
        } catch (error) {
            console.error('Photo processing failed:', error);
            setFormError(t('photoProcessingFailed'));
        }
    };

    const handleFieldChange = fieldName => event => {
        setFormFields({ ...formFields, [fieldName]: event.target.value });
    };

    const handleConfirmNewPoint = async event => {
        event.preventDefault();
        setFormError(null);

        // Validate user position is available
        if (!userPosition || userPosition.lat === null || userPosition.lng === null) {
            setFormError(t('locationNotAvailable'));
            return;
        }

        // Validate required fields are filled
        const emptyFields = [];
        locationSchema.obligatory_fields.forEach(([fieldName, fieldType]) => {
            if (fieldName === 'uuid') return; // Skip uuid - generated on backend

            const value = formFields[fieldName];
            const isEmpty =
                fieldType === 'list' ? !value || value.length === 0 : !value || value.trim() === '';

            if (isEmpty) {
                emptyFields.push(fieldName);
            }
        });

        if (emptyFields.length > 0) {
            setFormError(t('fillRequiredFields', { fields: emptyFields.join(', ') }));
            return;
        }

        const formData = new FormData();
        // Convert position from {lat, lng} to [lat, lng] array format
        formData.append('position', JSON.stringify([userPosition.lat, userPosition.lng]));
        if (photo) {
            formData.append('photo', photo);
        }

        // Add all dynamic form fields
        Object.entries(formFields).forEach(([fieldName, fieldValue]) => {
            if (Array.isArray(fieldValue)) {
                formData.append(fieldName, JSON.stringify(fieldValue));
            } else {
                formData.append(fieldName, fieldValue);
            }
        });

        try {
            const csrfToken = await getCsrfToken();
            await axios.post('/api/suggest-new-point', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'X-CSRFToken': csrfToken,
                },
            });
            toast.success(t('locationSuggestedSuccess'));

            // Reset form after successful submission
            setFormFields(initializeFormFields());
            setPhoto(null);
            setPhotoURL(null);

            // Close dialog only after successful submission
            setShowNewPointSuggestionBox(false);
        } catch (error) {
            console.error('Error suggesting new point:', error);
            // Surface the backend's specific reason (e.g. photo format/size) when available,
            // instead of a generic message that hides why the submission was rejected.
            setFormError(error.response?.data?.message || t('locationSuggestedError'));
            // Dialog stays open on error so user can retry
        }
    };

    // Static field name translations (for non-category fields)
    const staticFieldTranslations = {
        name: t('fieldName'),
    };

    // Helper to get translated field label
    const getFieldLabel = fieldName => {
        // Check static translations first, then category translations, then fallback to raw name
        return (
            staticFieldTranslations[fieldName] ||
            categoryTranslations.fieldNames[fieldName] ||
            fieldName
        );
    };

    // Helper to get translated option label
    const getOptionLabel = (fieldName, optionKey) => {
        return categoryTranslations.options[fieldName]?.[optionKey] || optionKey;
    };

    // Helper to get translated selected values for display
    const getSelectedDisplay = (fieldName, selectedValues) => {
        return selectedValues.map(val => getOptionLabel(fieldName, val)).join(', ');
    };

    // Render form field based on field type and whether it's a category
    const renderFormField = (fieldName, fieldType) => {
        const isCategory = fieldName in locationSchema.categories;
        const categoryOptions = isCategory ? locationSchema.categories[fieldName] : [];
        const fieldLabel = getFieldLabel(fieldName);

        if (fieldType === 'list' && isCategory) {
            // Multi-select for list categories
            return (
                <FormControl fullWidth margin="dense" key={fieldName}>
                    <InputLabel id={`${fieldName}-label`}>{fieldLabel}</InputLabel>
                    <Select
                        labelId={`${fieldName}-label`}
                        multiple
                        value={formFields[fieldName] || []}
                        onChange={handleFieldChange(fieldName)}
                        input={<OutlinedInput label={fieldLabel} />}
                        renderValue={selected => getSelectedDisplay(fieldName, selected)}
                        data-testid={`${fieldName}-select`}
                    >
                        {categoryOptions.map(option => (
                            <MenuItem key={option} value={option}>
                                <Checkbox checked={formFields[fieldName].includes(option)} />
                                <ListItemText primary={getOptionLabel(fieldName, option)} />
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            );
        } else if (isCategory) {
            // Single select for category fields
            return (
                <FormControl fullWidth margin="dense" key={fieldName}>
                    <InputLabel id={`${fieldName}-label`}>{fieldLabel}</InputLabel>
                    <Select
                        labelId={`${fieldName}-label`}
                        value={formFields[fieldName] || ''}
                        onChange={handleFieldChange(fieldName)}
                        data-testid={`${fieldName}-select`}
                    >
                        {categoryOptions.map(option => (
                            <MenuItem key={option} value={option}>
                                {getOptionLabel(fieldName, option)}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            );
        } else {
            // Text field for non-category fields
            return (
                <TextField
                    key={fieldName}
                    label={fieldLabel}
                    value={formFields[fieldName] || ''}
                    onChange={handleFieldChange(fieldName)}
                    fullWidth
                    margin="dense"
                    data-testid={`${fieldName}-input`}
                />
            );
        }
    };

    return (
        <>
            <Tooltip
                title={locationGranted ? t('suggestNewPoint') : t('locationServicesDisabled')}
                placement="left"
                arrow
                enterTouchDelay={0}
                leaveTouchDelay={1500}
            >
                <Button
                    onClick={handleNewPointButton}
                    variant="contained"
                    data-testid="suggest-new-point"
                    sx={{
                        ...buttonStyle,
                        ...getLocationAwareStyles(locationGranted),
                    }}
                >
                    <AddIcon style={{ color: 'white', fontSize: 24 }} />
                </Button>
            </Tooltip>

            <Dialog open={showNewPointBox} onClose={handleCloseNewPointBox}>
                <DialogTitle>{t('suggestNewPointDialogTitle')}</DialogTitle>
                <form onSubmit={handleConfirmNewPoint}>
                    <DialogContent>
                        {formError && (
                            <Alert severity="error" sx={{ mb: 2 }}>
                                {formError}
                            </Alert>
                        )}
                        <Box display="flex" alignItems="center" gap={2}>
                            <TextField
                                label={t('yourPosition')}
                                value={
                                    userPosition ? `${userPosition.lat}, ${userPosition.lng}` : ''
                                }
                                disabled
                                fullWidth
                                margin="dense"
                            />
                            <IconButton onClick={handleLocateMe}>
                                <RefreshIcon />
                            </IconButton>
                        </Box>
                        <Button variant="contained" component="label">
                            <AddAPhotoIcon />
                            <input
                                type="file"
                                hidden
                                accept={photoInputAccept}
                                onChange={handlePhotoUpload}
                                data-testid="photo-of-point"
                            />
                        </Button>
                        {photoURL && (
                            <img
                                src={photoURL}
                                alt="Selected"
                                style={{ width: '100%', height: 'auto' }}
                            />
                        )}

                        {/* Dynamically render form fields based on schema */}
                        {locationSchema.obligatory_fields
                            .filter(([fieldName]) => fieldName !== 'uuid')
                            .map(([fieldName, fieldType]) => renderFormField(fieldName, fieldType))}
                    </DialogContent>
                    <DialogActions>
                        <Button type="submit" variant="contained" color="primary">
                            {t('submit')}
                        </Button>
                        <Button
                            onClick={handleCloseNewPointBox}
                            variant="outlined"
                            color="secondary"
                        >
                            {t('cancel')}
                        </Button>
                    </DialogActions>
                </form>
            </Dialog>
        </>
    );
};
