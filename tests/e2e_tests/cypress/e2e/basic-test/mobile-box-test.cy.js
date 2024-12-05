import { verifyArbitraryPopupContent, verifyProblemForm, expectedPlaces } from "./commons.js"

describe('Popup Tests on Mobile', () => {
  const viewports = ['iphone-x', 'iphone-6', 'ipad-2', 'samsung-s10'];

  viewports.forEach((viewport) => {

    it(`displays title and subtitle in the popup on ${viewport}`, () => {
      cy.on('window:before:load', (win) => {
        Object.defineProperty(win.navigator, 'userAgent', {
          value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
        });
      })
      cy.viewport(viewport);
      cy.visit('/');
      cy.wait(500);

      cy.window().then((win) => {
        cy.stub(win, 'open').as('openStub');
      });

      cy.get('.leaflet-marker-icon').first().click();
      cy.wait(500);

      cy.get('.leaflet-marker-icon').each(($marker) => {
        cy.wrap($marker).click();
        cy.wait(500);

        cy.get('.MuiDialogContent-root').should('exist')
          .within(() => {
            verifyArbitraryPopupContent(expectedPlaces);
            verifyProblemForm();
          });
        cy.get('.MuiIconButton-root').should('exist').then(($button) => {
          cy.wrap($button).click();
          cy.wait(500);
        });
      });
    });
  });
});
