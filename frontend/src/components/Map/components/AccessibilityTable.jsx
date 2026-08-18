import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';
import Arrow from '@mui/icons-material/ArrowLeftRounded';
import { IconButton } from '@mui/material';
import PropTypes from 'prop-types';
import { httpService } from '../../../services/http/httpService';
import FieldRenderer from '../../MarkerPopup/FieldRenderer';
import { useCategories } from '../../Categories/CategoriesContext';

/**
 * Accessibility table component that displays location data in a tabular format.
 * Fetches location data based on user position and selected categories.
 * Dynamically builds table headers from all unique data fields across all locations.
 * Provides a back button to return to map view.
 *
 * @param {Object} props - Component props
 * @param {Object} props.userPosition - User's current position
 * @param {number} props.userPosition.lat - Latitude coordinate
 * @param {number} props.userPosition.lng - Longitude coordinate
 * @param {Function} props.setIsAccessibilityTableOpen - Callback to close the table and return to map view
 * @returns {React.ReactElement} Table container with location data and back button
 */
const AccessibilityTable = ({ userPosition, setIsAccessibilityTableOpen }) => {
    const { categories } = useCategories();
    const { t } = useTranslation();

    const [data, setData] = useState(null);
    const [headers, setHeaders] = useState([]);
    const [rows, setRows] = useState([]);

    useEffect(() => {
        httpService
            .getLocationsData(userPosition.lat, userPosition.lng, categories)
            .then(places => {
                setData(places);
            });
    }, [categories, userPosition]);

    useEffect(() => {
        if (!data) {
            return;
        }
        try {
            const uniqueHeadersSet = new Set([t('title')]);
            data.forEach(place => {
                place.data.forEach(item => {
                    uniqueHeadersSet.add(item[0]);
                });
            });
            const orderedKeysArray = Array.from(uniqueHeadersSet);
            setHeaders(orderedKeysArray);

            const getArr = (placeItem, key) => {
                const item = placeItem.find(it => it[0] === key);
                return item || ['', '—'];
            };

            const rowsLocal = data.map(it => {
                const row = [it.title];
                // Skip first element (title) and iterate over remaining keys
                orderedKeysArray.slice(1).forEach(key => {
                    const [, value] = getArr(it.data, key);
                    row.push(Array.isArray(value) ? value.join(', ') : value);
                });
                return row;
            });
            setRows(rowsLocal);
        } catch (error) {
            console.log('AccessibilityTable: ', error);
        }
    }, [data, t]);

    return (
        <>
            <div>
                <IconButton onClick={() => setIsAccessibilityTableOpen(false)}>
                    <Arrow />
                </IconButton>
            </div>
            <TableContainer component={Paper}>
                <Table sx={{ minWidth: 650 }}>
                    <TableHead>
                        <TableRow>
                            {headers.map(header => (
                                <TableCell
                                    key={header}
                                    align="center"
                                    style={{
                                        fontWeight: 'bold',
                                    }}
                                >
                                    {header}
                                </TableCell>
                            ))}
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {rows.map(row => (
                            <TableRow
                                key={row.toString()}
                                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                            >
                                {row.map((cell, cellIndex) => (
                                    <TableCell key={headers[cellIndex]} align="center">
                                        {cell.type ? <FieldRenderer value={cell} /> : cell}
                                    </TableCell>
                                ))}
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </>
    );
};

AccessibilityTable.propTypes = {
    userPosition: PropTypes.shape({
        lat: PropTypes.number,
        lng: PropTypes.number,
    }).isRequired,
    setIsAccessibilityTableOpen: PropTypes.func.isRequired,
};

export default AccessibilityTable;
