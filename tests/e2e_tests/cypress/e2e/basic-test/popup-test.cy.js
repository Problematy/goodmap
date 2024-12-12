import { verifyPopupContent, expectedPlaceZwierzyniecka, getRightmostMarker } from "./commons.js"

describe("Popup Tests on desktop", () => {

  it("displays popup title, subtitle, categories and CTA", () => {
    cy.visit('/');

    cy.window().then((win) => {
      cy.stub(win, 'open').as('openStub');
    });

    cy.get('.leaflet-marker-icon').click();
    cy.get('.leaflet-marker-icon').should('have.length', 2);

    cy.get('.leaflet-marker-icon').then((markers) => {
      const rightmostMarker = getRightmostMarker(markers);
      cy.wrap(rightmostMarker).click();
    });

    cy.get('.leaflet-popup-content').should('exist').within(() => {
      verifyPopupContent(expectedPlaceZwierzyniecka);
      // TODO BUG: when problem form is opened on desktop, the close button may be hidden
      // Fix this and add checking problem form in this test
    });
    cy.get('.leaflet-popup-close-button').should('exist').click();
  });
});
