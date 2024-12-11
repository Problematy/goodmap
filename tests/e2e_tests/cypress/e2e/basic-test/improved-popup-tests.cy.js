import { verifyPopupContent, expectedPlaces, getRightmostMarker } from "./commons.js"

describe("Improved Popup Tests", () => {
  beforeEach(() => {
    cy.visit('/');
  })

  it("displays popup subtitle and categories and CTA", () => {
    cy.window().then((win) => {
      cy.stub(win, 'open').as('openStub');
    });

    cy.get('.leaflet-marker-icon').click();
    cy.get('.leaflet-marker-icon').should('have.length', 2);

    cy.get('.leaflet-marker-icon').then((markers) => {
        const rightmostMarker = getRightmostMarker(markers);
        cy.wrap(rightmostMarker).click();
    });

    cy.get('.leaflet-popup-content').should('exist')
      .within(() => {
        verifyPopupContent(expectedPlaces[1]);
      });

    cy.get('.leaflet-popup-close-button').should('exist').then(($button) => {
      cy.wrap($button).click();
    });
  });
});
