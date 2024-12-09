import { verifyPopupContent, expectedPlaces } from "./commons.js"


describe("Recording 09/12/2024 at 11:45:39", () => {
  beforeEach(() => {
    cy.visit('/');
    cy.wait(500);
  })
  it("tests Recording 09/12/2024 at 11:45:39", () => {
    cy.get('.leaflet-marker-icon > div').click();
    cy.wait(1000)
    cy.get('[style="margin-left: -12px; margin-top: -41px; width: 25px; height: 41px; transform: translate3d(451px, 333px, 0px); z-index: 333; opacity: 1;"]').click();
    cy.get('.leaflet-popup-content').should('exist')
      .within(() => {
        verifyPopupContent(expectedPlaces[1]);
      });

    cy.get('[style="cursor: pointer; text-align: right; color: red; margin-top: 5px; margin-bottom: 5px;"]').click();
    cy.get('.sc-egkSDF').select('broken');
    cy.get('.sc-dntaoT').click();
    cy.get('.leaflet-popup-close-button > span').click();
  });
});
