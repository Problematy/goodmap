describe('Go To My Location Button', () => {
    beforeEach(() => {
        cy.visit('/', {
            onBeforeLoad(win) {
                // Mock the geolocation API
                cy.stub(win.navigator.geolocation, 'getCurrentPosition').callsFake((success) => {
                    success({
                        coords: {
                            latitude: 37.7749, // Mock latitude
                            longitude: -122.4194, // Mock longitude
                            accuracy: 100, // Mock accuracy in meters
                        },
                    });
                });

                cy.stub(win.navigator.geolocation, 'watchPosition').callsFake((success) => {
                    success({
                        coords: {
                            latitude: 37.7749, // Mock latitude
                            longitude: -122.4194, // Mock longitude
                            accuracy: 100, // Mock accuracy in meters
                        },
                    });
                });
            },
        });
    });

    it('should click the go-to-my-location button and move the map', () => {
        // Allow location services (if prompted)
        cy.window().then((win) => {
            win.navigator.permissions.query = () =>
                Promise.resolve({
                    state: 'granted', // Mock permission as granted
                });
        });
        cy.get('.leaflet-marker-icon').click();


        cy.get('.MuiButtonBase-root > [data-testid="MyLocationIcon"] > path').click();
        cy.wait(500);
        cy.get('.MuiButtonBase-root > [data-testid="MyLocationIcon"] > path').click();
        cy.wait(8000);
        cy.intercept('GET', 'https://c.tile.openstreetmap.org/16/10484/25329.png').as('tileRequest');
        cy.wait('@tileRequest').then((interception) => {
            expect(interception.response.statusCode).to.eq(200); // Assert the status code
            expect(interception.request.url).to.include('10484/25329.png'); // Assert the URL
        });

    });
});
