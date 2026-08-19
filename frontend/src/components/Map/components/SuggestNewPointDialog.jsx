import React, { useState, useEffect, useRef, useMemo } from 'react';
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
    Alert,
    CircularProgress,
} from '@mui/material';
import PropTypes from 'prop-types';

import AddAPhotoIcon from '@mui/icons-material/AddAPhoto';
import RefreshIcon from '@mui/icons-material/Refresh';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import imageCompression from 'browser-image-compression';
import getCsrfToken from '../../../utils/csrf';
import { useLocationSchema } from '../context/LocationSchemaContext';
import { useLocation } from '../context/LocationContext';
import { useCategories } from '../../Categories/CategoriesContext';
import toast from '../../../utils/toast';

// Map a category's options to a { key: translation } object.
// Options come as [[key, translation], ...] or [key, ...].
const mapCategoryOptions = categoryOptions => {
    const optionMap = {};
    categoryOptions.forEach(opt => {
        if (Array.isArray(opt)) {
            const [key, value] = opt;
            optionMap[key] = value;
        } else {
            optionMap[opt] = opt;
        }
    });
    return optionMap;
};

// Build { fieldNames, options } translation maps from the fetched category definitions.
const buildCategoryTranslations = categoriesData => {
    const fieldNames = {};
    const options = {};

    categoriesData.forEach(({ categoryKey, categoryName, options: categoryOptions }) => {
        fieldNames[categoryKey] = categoryName;

        if (categoryOptions?.length) {
            options[categoryKey] = mapCategoryOptions(categoryOptions);
        }
    });

    return { fieldNames, options };
};

const isFieldEmpty = (value, fieldType) =>
    fieldType === 'list' ? !value || value.length === 0 : !value || value.trim() === '';

const findEmptyRequiredFields = (obligatoryFields, formFields) =>
    obligatoryFields
        .filter(([fieldName]) => fieldName !== 'uuid')
        .filter(([fieldName, fieldType]) => isFieldEmpty(formFields[fieldName], fieldType))
        .map(([fieldName]) => fieldName);

// The backend expects the whole non-photo payload as one JSON object in the
// 'location' field, so it doesn't need to know per-field which values are
// JSON-encoded.
const buildSuggestionFormData = ({ userPosition, photo, formFields }) => {
    const formData = new FormData();
    formData.append(
        'location',
        JSON.stringify({
            position: [userPosition.lat, userPosition.lng],
            ...formFields,
        }),
    );
    if (photo) {
        formData.append('photo', photo);
    }
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
 * Dialog form for suggesting a new map point. Fields are generated dynamically from the
 * deployment's location schema and include the user's position, an optional photo, and
 * every obligatory location attribute defined by the backend.
 *
 * @param {{open: boolean, onClose: () => void}} props
 * @returns {React.ReactElement} Dialog with the new point suggestion form
 */
const SuggestNewPointDialog = ({ open, onClose }) => {
    const { t } = useTranslation();
    const { userPosition, requestLocationWithFeedback } = useLocation();
    const { categoriesData } = useCategories();
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
    const categoryTranslations = useMemo(
        () => buildCategoryTranslations(categoriesData),
        [categoriesData],
    );

    // A notice from a previous attempt must not greet the user on reopen.
    useEffect(() => {
        if (open) {
            setFormNotice(null);
        }
    }, [open]);

    const { locationSchema } = useLocationSchema();
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

    // The schema is fetched, so it is empty on the first render and the initial state
    // above has nothing to build from. Rebuild the fields once it arrives.
    useEffect(() => {
        setFormFields(initializeFormFields());
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [locationSchema]);

    const handleLocateMe = () => {
        requestLocationWithFeedback();
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
            onClose();
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
    // Check static translations first, then category translations, then fallback to raw name
    const getFieldLabel = fieldName =>
        staticFieldTranslations[fieldName] ||
        categoryTranslations.fieldNames[fieldName] ||
        fieldName;

    // Helper to get translated option label
    const getOptionLabel = (fieldName, optionKey) =>
        categoryTranslations.options[fieldName]?.[optionKey] || optionKey;

    // Helper to get translated selected values for display
    const getSelectedDisplay = (fieldName, selectedValues) =>
        selectedValues.map(val => getOptionLabel(fieldName, val)).join(', ');

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
                                <Checkbox
                                    checked={(formFields[fieldName] || []).includes(option)}
                                />
                                <ListItemText primary={getOptionLabel(fieldName, option)} />
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            );
        }
        if (isCategory) {
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
        }
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
    };

    return (
        <Dialog open={open} onClose={onClose} PaperProps={{ ref: dialogPaperRef }}>
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
                            value={userPosition ? `${userPosition.lat}, ${userPosition.lng}` : ''}
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
                        onClick={onClose}
                        variant="outlined"
                        color="secondary"
                        disabled={isSubmitting}
                    >
                        {t('cancel')}
                    </Button>
                </DialogActions>
            </form>
        </Dialog>
    );
};

SuggestNewPointDialog.propTypes = {
    open: PropTypes.bool.isRequired,
    onClose: PropTypes.func.isRequired,
};

export default SuggestNewPointDialog;
