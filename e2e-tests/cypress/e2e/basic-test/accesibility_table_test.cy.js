import { fakeLocation } from '../../utils/fake-location';

function rowElements() {
    return cy.get('tr');
}

describe('Accessibility table test', () => {
    beforeEach(() => {
        const latitude = 51.10655;
        const longitude = 17.0555;
        cy.visit('/', fakeLocation(latitude, longitude));
        // Wait for map markers to load before clicking list view button
        cy.get('.leaflet-marker-icon', { timeout: 10000 }).should('exist');
        cy.get('button[id="listViewButton"]', { timeout: 10000 }).should('be.visible').click();
        // Wait for table to appear after clicking list view
        cy.get('table', { timeout: 10000 }).should('be.visible');
    });

    it('should properly display places', () => {
        rowElements()
            // Header + 2 rows
            .should('have.length', 3);
    });

    it("should 'Zwierzyniecka' be first row", () => {
        rowElements().eq(1).find('td').should('contain', 'Zwierzyniecka');
    });
});
