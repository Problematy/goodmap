import React, { useState, useEffect, useRef } from 'react';
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
    CircularProgress,
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
import imageCompression from 'browser-image-compression';

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

const isFieldEmpty = (value, fieldType) =>
    fieldType === 'list' ? !value || value.length === 0 : !value || value.trim() === '';

const findEmptyRequiredFields = (obligatoryFields, formFields) =>
    obligatoryFields
        .filter(([fieldName]) => fieldName !== 'uuid')
        .filter(([fieldName, fieldType]) => isFieldEmpty(formFields[fieldName], fieldType))
        .map(([fieldName]) => fieldName);

const buildSuggestionFormData = ({ userPosition, photo, formFields }) => {
    const formData = new FormData();
    formData.append('position', JSON.stringify([userPosition.lat, userPosition.lng]));
    if (photo) {
        formData.append('photo', photo);
    }
    Object.entries(formFields).forEach(([fieldName, fieldValue]) => {
        formData.append(
            fieldName,
            Array.isArray(fieldValue) ? JSON.stringify(fieldValue) : fieldValue,
        );
    });
    return formData;
};

// For display only - the byte count stays authoritative for size checks.
const toMiB = bytes => Number((bytes / 1024 / 1024).toFixed(1));

const isPositionAvailable = position =>
    Boolean(position) && position.lat !== null && position.lng !== null;

// Scrolls the returned element back to the top whenever `trigger` becomes truthy.
// Attach to the Dialog's Paper - it's the scroll container, not DialogContent.
const useScrollToTop = trigger => {
    const ref = useRef(null);
    useEffect(() => {
        if (trigger) {
            ref.current?.scrollTo?.({ top: 0, behavior: 'smooth' });
        }
    }, [trigger]);
    return ref;
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
    // Shown inline in the dialog: a toast here can end up behind it.
    // 'warning' notices are non-blocking, 'error' ones stop submission.
    const [formNotice, setFormNotice] = useState(null);
    const showError = message => setFormNotice({ severity: 'error', message });
    const showWarning = message => setFormNotice({ severity: 'warning', message });
    const dialogPaperRef = useScrollToTop(formNotice);
    const [isCompressingPhoto, setIsCompressingPhoto] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
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
            setFormNotice(null);
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
        setPhoto(file);
        setPhotoURL(URL.createObjectURL(file));
    };

    const compressAndAcceptPhoto = async file => {
        const maxSizeMiB = toMiB(maxPhotoSizeBytes);
        showWarning(t('photoWillBeCompressed', { maxSizeMiB }));
        setIsCompressingPhoto(true);
        try {
            const compressed = await imageCompression(file, {
                maxSizeMB: maxPhotoSizeBytes / 1024 / 1024,
                maxWidthOrHeight: 1920,
                fileType: 'image/jpeg',
                useWebWorker: true,
            });
            if (compressed.size > maxPhotoSizeBytes) {
                showError(t('fileTooLarge', { maxSizeMiB }));
                return;
            }
            acceptPhoto(compressed);
            showWarning(t('photoCompressed', { maxSizeMiB }));
        } catch (error) {
            console.error('Photo processing failed:', error);
            showError(t('photoProcessingFailed'));
        } finally {
            setIsCompressingPhoto(false);
        }
    };

    const handlePhotoUpload = async event => {
        const file = event.target.files[0];
        if (!file) {
            return;
        }
        setFormNotice(null);

        if (!allowedPhotoMimeTypes.includes(file.type)) {
            showError(
                t('unsupportedPhotoFormat', {
                    allowedFormats: allowedPhotoExtensions.map(ext => ext.toUpperCase()).join('/'),
                }),
            );
            return;
        }

        if (file.size <= maxPhotoSizeBytes) {
            acceptPhoto(file);
            return;
        }

        await compressAndAcceptPhoto(file);
    };

    const handleFieldChange = fieldName => event => {
        setFormFields({ ...formFields, [fieldName]: event.target.value });
    };

    const handleConfirmNewPoint = async event => {
        event.preventDefault();
        setFormNotice(null);

        if (!isPositionAvailable(userPosition)) {
            showError(t('locationNotAvailable'));
            return;
        }

        const emptyFields = findEmptyRequiredFields(locationSchema.obligatory_fields, formFields);
        if (emptyFields.length > 0) {
            showError(t('fillRequiredFields', { fields: emptyFields.join(', ') }));
            return;
        }

        const formData = buildSuggestionFormData({ userPosition, photo, formFields });

        setIsSubmitting(true);
        try {
            const csrfToken = await getCsrfToken();
            await axios.post('/api/suggest-new-point', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'X-CSRFToken': csrfToken,
                },
            });
            toast.success(t('locationSuggestedSuccess'));

            setFormFields(initializeFormFields());
            setPhoto(null);
            setPhotoURL(null);
            setShowNewPointSuggestionBox(false);
        } catch (error) {
            console.error('Error suggesting new point:', error);
            showError(error.response?.data?.message || t('locationSuggestedError'));
        } finally {
            setIsSubmitting(false);
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

            <Dialog
                open={showNewPointBox}
                onClose={handleCloseNewPointBox}
                PaperProps={{ ref: dialogPaperRef }}
            >
                <DialogTitle>{t('suggestNewPointDialogTitle')}</DialogTitle>
                <form onSubmit={handleConfirmNewPoint}>
                    <DialogContent>
                        {formNotice && (
                            <Alert severity={formNotice.severity} sx={{ mb: 2 }}>
                                {formNotice.message}
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
                        <Button variant="contained" component="label" disabled={isCompressingPhoto}>
                            {isCompressingPhoto ? (
                                <CircularProgress size={24} color="inherit" />
                            ) : (
                                <AddAPhotoIcon />
                            )}
                            <input
                                type="file"
                                hidden
                                accept={photoInputAccept}
                                onChange={handlePhotoUpload}
                                disabled={isCompressingPhoto}
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
                        <Button
                            type="submit"
                            variant="contained"
                            color="primary"
                            disabled={isSubmitting}
                            aria-label={t('submit')}
                        >
                            {isSubmitting ? (
                                <CircularProgress size={20} color="inherit" />
                            ) : (
                                t('submit')
                            )}
                        </Button>
                        <Button
                            onClick={handleCloseNewPointBox}
                            variant="outlined"
                            color="secondary"
                            disabled={isSubmitting}
                        >
                            {t('cancel')}
                        </Button>
                    </DialogActions>
                </form>
            </Dialog>
        </>
    );
};
