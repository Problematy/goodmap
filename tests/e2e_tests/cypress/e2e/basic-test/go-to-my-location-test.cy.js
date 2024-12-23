function lon2tile(lon, zoom) {
    return Math.floor(((lon + 180) / 360) * Math.pow(2, zoom));
}
function lat2tile(lat, zoom) {
    return Math.floor(
        ((1 -
            Math.log(Math.tan((lat * Math.PI) / 180) + 1 / Math.cos((lat * Math.PI) / 180)) /
                Math.PI) /
            2) *
            Math.pow(2, zoom),
    );
}

let mockedLat = 51.919126;
let mockedLon = 15.976627;

describe('Go To My Location Button', () => {
    beforeEach(() => {
        cy.visit('/', {
            onBeforeLoad(win) {
                // Mock the geolocation API
                cy.stub(win.navigator.geolocation, 'getCurrentPosition').callsFake(success => {
                    success({
                        coords: {
                            latitude: mockedLat, // Mock latitude
                            longitude: mockedLon, // Mock longitude
                            accuracy: 100, // Mock accuracy in meters
                        },
                    });
                });

                cy.stub(win.navigator.geolocation, 'watchPosition').callsFake(success => {
                    success({
                        coords: {
                            latitude: mockedLat, // Mock latitude
                            longitude: mockedLon, // Mock longitude
                            accuracy: 100, // Mock accuracy in meters
                        },
                    });
                });
            },
        });
    });

    it('should click the go-to-my-location button and move the map', () => {
        // Allow location services (if prompted)
        cy.window().then(win => {
            win.navigator.permissions.query = () =>
                Promise.resolve({
                    state: 'granted', // Mock permission as granted
                });
        });
        cy.get('.leaflet-marker-icon').click();

        cy.get('.MuiButtonBase-root > [data-testid="MyLocationIcon"] > path').click();
        cy.get('.MuiButtonBase-root > [data-testid="MyLocationIcon"] > path').click();
        const zoomLevel = 16;
        const expectedLat = lat2tile(mockedLat, zoomLevel);
        const expectedLon = lon2tile(mockedLon, zoomLevel);
        cy.log(`Expected lat: ${expectedLat}, Expected lon: ${expectedLon}`);
        const regExpURL = new RegExp(`^https://[abc]\\.tile\\.openstreetmap\\.org/${zoomLevel}/${expectedLon}/${expectedLat}\\.png$`);
        cy.intercept('GET', regExpURL).as('tileRequest');
        cy.wait('@tileRequest', {timeout: 10000}).then(interception => {
            expect(interception.response.statusCode).to.eq(200);
            expect(interception.request.url).to.include(`${expectedLon}/${expectedLat}.png`);
        });
    });
});
