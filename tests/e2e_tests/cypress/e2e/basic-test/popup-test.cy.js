import { verifyArbitraryPopupContent, expectedPlaces } from "./commons.js"

describe('Popup Tests', () => {
  beforeEach(() => {
    cy.visit('/');
    cy.wait(500);
  })

  it('displays title and subtitle in the popup', () => {
    cy.window().then((win) => {
      cy.stub(win, 'open').as('openStub');
    });

    cy.get('.leaflet-marker-icon').first().click();
    cy.wait(500);

    cy.get('.leaflet-marker-icon').each(($marker) => {
      cy.wrap($marker).click();
      cy.wait(500);
      cy.get('.leaflet-popup-content').should('exist')
        .within(() => {
          verifyArbitraryPopupContent(expectedPlaces);

          // TODO BUG: when problem form is opened on desktop, the close button may be hidden
          // Fix this and add checking problem form in this test
        });
      cy.get('.leaflet-popup-close-button').should('exist').then(($button) => {
        cy.wrap($button).click();
        cy.wait(500);
      });
    });
  });
});
