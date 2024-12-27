// Checks whether map has moved to the correct location by checking
// if the specific OSM (Open Street Map) tile file was requested.
// Filename (URL) format is /zoom/column/tile.png
// Formulas that calculate tiles and columns can be found here:
// https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Common_programming_languages
function lon2column(lon, zoom) {
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

let mockedLon = 15.976627;
let mockedLat = 51.919126;

describe('Go To My Location Button', () => {
    beforeEach(() => {
        cy.visit('/', {
            onBeforeLoad(win) {
                cy.stub(win.navigator.geolocation, 'watchPosition').callsFake(success => {
                    success({
                        coords: {
                            longitude: mockedLon,
                            latitude: mockedLat,
                            accuracy: 100,
                        },
                    });
                });
            },
        });
    });

    it('should click the go-to-my-location button and move the map', () => {
        cy.window().then(win => {
            win.navigator.permissions.query = () =>
                Promise.resolve({
                    state: 'granted',
                });
        });
        cy.get('.leaflet-marker-icon').click();

        cy.get('.MuiButtonBase-root > [data-testid="MyLocationIcon"] > path').click();
        cy.get('.MuiButtonBase-root > [data-testid="MyLocationIcon"] > path').click();

        const zoomLevel = 16;
        const OSMColumn = lon2column(mockedLon, zoomLevel);
        const OSMTile = lat2tile(mockedLat, zoomLevel);

        const regExpURL = new RegExp(
            `^https://[abc]\\.tile\\.openstreetmap\\.org/${zoomLevel}/${OSMColumn}/${OSMTile}\\.png$`,
        );
        cy.intercept('GET', regExpURL).as('tileRequest');
        cy.wait('@tileRequest', { timeout: 10000 }).then(interception => {
            expect(interception.response.statusCode).to.eq(200);
            expect(interception.request.url).to.include(`${OSMColumn}/${OSMTile}.png`);
        });
    });
});
