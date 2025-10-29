import { fakeLocation } from '../../utils/fake-location';

const RysyMountainLat = 49.179;
const RysyMountainLon = 20.088;
const RysyTileURL = 'https://c.tile.openstreetmap.org/16/36424/22456.png';

describe('Go To My Location Button', () => {
    beforeEach(() => {
        cy.visit('/', fakeLocation(RysyMountainLat, RysyMountainLon));
    });

    it('should click the go-to-my-location button and move the map', () => {
        cy.get('.MuiButtonBase-root > [data-testid="MyLocationIcon"] > path').click();
        cy.get('.leaflet-tile-container > img', { timeout: 10000 }).should(
            'have.attr',
            'src',
            RysyTileURL,
        );
    });
});
