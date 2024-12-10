import { verifyPopupContent, expectedPlaces } from "./commons.js"


describe("Recording 09/12/2024 at 11:45:39", () => {
  beforeEach(() => {
    cy.visit('/');
    cy.wait(500);
  })
  const wait_duration = 100;

  it("tests Recording 09/12/2024 at 11:45:39", () => {
    cy.window().then((win) => {
      cy.stub(win, 'open').as('openStub');
    });

    cy.get('.leaflet-marker-icon > div').click();
    cy.wait(wait_duration);

    // Wait for the markers to appear
    cy.get('.leaflet-marker-icon').should('have.length', 2);

       // Find the rightmost marker
    cy.get('.leaflet-marker-icon').then((markers) => {
    let rightmostMarker;
      let maxX = -Infinity;

      // Loop through all markers to find the one with the greatest x position
      Cypress.$(markers).each((index, marker) => {
        const rect = marker.getBoundingClientRect(); // Get marker position
        if (rect.x > maxX) {
          maxX = rect.x;
          rightmostMarker = marker;
        }
      });
    cy.wrap(rightmostMarker).click();

    });

    cy.wait(wait_duration);
    cy.get('.leaflet-popup-content').should('exist')
      .within(() => {
        verifyPopupContent(expectedPlaces[1]);
      });

    cy.get('.leaflet-popup-close-button > span').click();

  });
});
