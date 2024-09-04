import React, { useState } from 'react';
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
    Snackbar,
    IconButton,
} from '@mui/material';

import AddAPhotoIcon from '@mui/icons-material/AddAPhoto';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import Control from 'react-leaflet-custom-control';
import axios from 'axios';
import { buttonStyle } from '../../../styles/buttonStyle';
import { useEffect } from 'react';

export const SuggestNewPointButton = () => {
    const [userPosition, setUserPosition] = useState({ lat: null, lng: null });

    useEffect(() => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                position => {
                    setUserPosition({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                    });
                },
                () => {
                    setSnackbarMessage('Please enable location services to suggest a new point.');
                    setSnackbarOpen(true);
                },
            );
        } else {
            setSnackbarMessage('Geolocation is not supported by this browser.');
            setSnackbarOpen(true);
        }
    }, []);

    const [showNewPointBox, setShowNewPointSuggestionBox] = useState(false);
    const [snackbarOpen, setSnackbarOpen] = useState(false);
    const [snackbarMessage, setSnackbarMessage] = useState('');
    const [photo, setPhoto] = useState(null);
    const [photoURL, setPhotoURL] = useState(null);
    const [organization, setOrganization] = useState('');

    const handleNewPointButton = () => {
        if (!navigator.geolocation) {
            setSnackbarMessage('Please enable location services to suggest a new point.');
            setSnackbarOpen(true);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            () => setShowNewPointSuggestionBox(true),
            () => {
                setSnackbarMessage('Please enable location services to suggest a new point.');
                setSnackbarOpen(true);
            },
        );
    };

    const handleLocateMe = () => {
        if (!navigator.geolocation) {
            setSnackbarMessage('Please enable location services to suggest a new point.');
            setSnackbarOpen(true);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            position =>
                setUserPosition({ lat: position.coords.latitude, lng: position.coords.longitude }),
            () => {
                setSnackbarMessage('Please enable location services to suggest a new point.');
                setSnackbarOpen(true);
            },
        );
    };

    const handleCloseNewPointBox = () => {
        setShowNewPointSuggestionBox(false);
    };

    const handleSnackbarClose = (event, reason) => {
        if (reason === 'clickaway') {
            return;
        }

        setSnackbarOpen(false);
    };

    const handlePhotoUpload = event => {
        const file = event.target.files[0];
        const fileSizeMB = file.size / 1024 / 1024;
        if (fileSizeMB > 5) {
            setSnackbarMessage(
                'The selected file is too large. Please select a file smaller than 5MB.',
            );
            setSnackbarOpen(true);
            return;
        }
        setPhoto(file);
        setPhotoURL(URL.createObjectURL(file));
    };

    const handleOrganizationChange = event => {
        setOrganization(event.target.value);
    };

    const handleConfirmNewPoint = async event => {
        event.preventDefault();
        setShowNewPointSuggestionBox(false);

        const formData = new FormData();
        formData.append('position', JSON.stringify(userPosition));
        formData.append('photo', photo);
        formData.append('organization', organization);

        try {
            await axios.post('/api/suggest-new-point', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
        } catch (error) {
            console.error('Error suggesting new point:', error);
        }
    };

    // TODO - fetch organizations from the backend
    const organizations = [
        { id: 'org-1', name: 'ORG 1' },
        { id: 'org-2', name: 'ORG 2' },
        { id: 'org-3', name: 'ORG 3' },
    ];

    return (
        <>
            <Button
                onClick={handleNewPointButton}
                style={buttonStyle}
                variant="contained"
                data-testid="suggest-new-point"
            >
                <AddIcon style={{ color: 'white', fontSize: 24 }} />
            </Button>

            <Dialog open={showNewPointBox} onClose={handleCloseNewPointBox}>
                <DialogTitle>Suggest a New Point</DialogTitle>
                <form onSubmit={handleConfirmNewPoint}>
                    <DialogContent>
                        <Box display="flex" alignItems="center" gap={2}>
                            <TextField
                                label="Your Position"
                                value={`${userPosition.lat}, ${userPosition.lng}`}
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
                        <FormControl fullWidth margin="dense">
                            <InputLabel id="organization-label">Organization</InputLabel>
                            <Select
                                labelId="organization-label"
                                value={organization}
                                onChange={handleOrganizationChange}
                                data-testid="organization-select"
                            >
                                {organizations.map(org => (
                                    <MenuItem key={org.id} value={org.id}>
                                        {org.name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </DialogContent>
                    <DialogActions>
                        <Button type="submit" variant="contained" color="primary">
                            Submit
                        </Button>
                        <Button
                            onClick={handleCloseNewPointBox}
                            variant="outlined"
                            color="secondary"
                        >
                            Cancel
                        </Button>
                    </DialogActions>
                </form>
            </Dialog>
            <Snackbar
                open={snackbarOpen}
                autoHideDuration={6000}
                onClose={handleSnackbarClose}
                message={snackbarMessage}
            />
        </>
    );
};
