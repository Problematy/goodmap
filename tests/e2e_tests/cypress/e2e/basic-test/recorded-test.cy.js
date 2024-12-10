import { verifyPopupContent, expectedPlaces } from "./commons.js"


describe("Recording 09/12/2024 at 11:45:39", () => {
  beforeEach(() => {
    cy.visit('/');
    cy.wait(500);
  })
  it("tests Recording 09/12/2024 at 11:45:39", () => {
    cy.window().then((win) => {
      cy.stub(win, 'open').as('openStub');
    });
    cy.get('.leaflet-marker-icon > div').click();
    cy.wait(1000)
    cy.get('[style="margin-left: -12px; margin-top: -41px; width: 25px; height: 41px; transform: translate3d(451px, 333px, 0px); z-index: 333; opacity: 1;"]').click();
    cy.wait(1000)
    cy.get('.leaflet-popup-content').should('exist')
      .within(() => {
        verifyPopupContent(expectedPlaces[1]);
      });

    cy.wait(1000)
    cy.get('.leaflet-popup-close-button > span').click();
    cy.wait(1000)

    /* ==== Generated with Cypress Studio ==== */
    cy.get('[style="margin-left: -12px; margin-top: -41px; width: 25px; height: 41px; transform: translate3d(381px, 223px, 0px); z-index: 223; opacity: 1;"]').click();
    cy.get('b > button').click();
    cy.get('.leaflet-popup-close-button > span').click();
    /* ==== End Cypress Studio ==== */
  });
});
