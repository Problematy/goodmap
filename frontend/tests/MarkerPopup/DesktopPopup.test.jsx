import React from 'react';
import PropTypes from 'prop-types';
import '@testing-library/jest-dom';
import { render, act, fireEvent } from '@testing-library/react';
import { MapContainer, Marker } from 'react-leaflet';
import { Popup as LeafletPopup } from 'leaflet';
import DesktopPopup from '../../src/components/MarkerPopup/DesktopPopup';

// Content the way the server sends it: markup React does not own, so React never sees the
// image's `load` - only the browser does.
const ServerImage = () => (
    // eslint-disable-next-line react/no-danger -- stands in for serverHtmlField's markup
    <span dangerouslySetInnerHTML={{ __html: '<img src="https://example.com/a.jpg" alt="">' }} />
);

const TestMap = ({ withPopup }) => (
    <MapContainer center={[51.1, 17.05]} zoom={10} style={{ height: '100vh' }}>
        <Marker position={[51.1, 17.05]}>
            {withPopup && (
                <DesktopPopup>
                    <ServerImage />
                </DesktopPopup>
            )}
        </Marker>
    </MapContainer>
);

TestMap.propTypes = { withPopup: PropTypes.bool.isRequired };

// As in the app: the marker is on the map first, and the popup mounts once it is clicked.
const renderPopup = async () => {
    const { rerender } = render(<TestMap withPopup={false} />);
    await act(async () => rerender(<TestMap withPopup />));
};

describe('DesktopPopup', () => {
    let update;

    beforeEach(() => {
        update = jest.spyOn(LeafletPopup.prototype, 'update');
    });

    afterEach(() => {
        update.mockRestore();
    });

    it.each(['load', 'error'])(
        're-lays out and re-pans the popup when an image in it fires %s',
        async eventName => {
            await renderPopup();
            const img = document.querySelector('.leaflet-popup-content img');
            expect(img).toBeInTheDocument();
            update.mockClear();

            fireEvent(img, new Event(eventName));

            expect(update).toHaveBeenCalledTimes(1);
        },
    );
});
