import {zoomInMap, verifyPopupContent, verifyArbitraryPopupContent, verifyProblemForm} from "./commons.js"


describe('Popup Tests', () => {
  beforeEach(() => {
    cy.visit('/');
    cy.wait(1000);
  })
  const expectedPlace1 = {
    title: "Grunwaldzki",
    subtitle: "big bridge",
    categories: [
      ["type_of_place", "big bridge"],
      ["accessible_by", "pedestrians, cars"]
    ],
    CTA: {
      "type": "CTA",
      "value": "https://www.example.com",
      "displayValue": "Visit example.org!"
    }
  }
  const expectedPlace2 = {
    title: "Zwierzyniecka",
    subtitle: "small bridge",
    categories: [
      ["type_of_place", "small bridge"],
      ["accessible_by", "bikes, pedestrians"]
    ]
  }
const expectedPlaces = [expectedPlace1, expectedPlace2];


  it('displays title and subtitle in the popup', () => {
    cy.window().then((win) => {
      cy.stub(win, 'open').as('openStub');
    });

    zoomInMap();

    cy.get('.leaflet-marker-icon').each(($marker) => {
      cy.wrap($marker).click();
      cy.wait(500);
      cy.get('.leaflet-popup-content').should('exist')
        .within(() => {
          verifyArbitraryPopupContent(expectedPlaces);

//          verifyProblemForm();
        });
      cy.get('.leaflet-popup-close-button').should('exist').then(($button) => {
        cy.wrap($button).click();
        cy.wait(500);
      });
    });
  });
});
