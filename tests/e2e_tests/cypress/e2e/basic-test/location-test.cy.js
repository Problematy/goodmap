describe('Geolocation Request Test', () => {
  it('Checks if page is asking for geolocation on load', () => {
    cy.visit('/', {
      onBeforeLoad ({ navigator }) {
        cy.spy(navigator.geolocation, 'watchPosition').as('geonavigator');
      }
    });
    cy.get('@geonavigator').should('be.calledOnce');
  });
});
