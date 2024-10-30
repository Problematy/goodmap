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

  it('displays title and subtitle in the popup', () => {
    cy.window().then((win) => {
      cy.stub(win, 'open').as('openStub');
    });

    const zoomInTimes = 1;
    for (let i = 0; i < zoomInTimes; i++) {
      cy.get('.leaflet-marker-icon').first().click();
      cy.wait(500);
    }

    // TODO - Find a way to search for a specific point, not iterate over all of them
    cy.get('.leaflet-marker-icon').each(($marker) => {
      cy.wrap($marker).click();
      cy.wait(500);

      cy.get('.leaflet-popup-content').should('exist')
        .within(() => {
          function verifyPopupContent(expectedContent) {
            cy.get('.point-subtitle')
              .should('have.text', expectedContent.subtitle);

            expectedContent.categories.forEach(([category, value]) => {
              cy.contains(category).should('exist');
              cy.contains(value).should('exist');
            });

            if (expectedContent.CTA) {
              cy.contains(expectedContent.CTA.displayValue).should('exist');
              cy.contains('button', expectedContent.CTA.displayValue).click();
              cy.get('@openStub').should('have.been.calledOnceWith',
                expectedContent.CTA.value, '_blank');
            }
          }

          cy.get('.point-title').should('exist').invoke('text')
            .then((title) => {
              if (title === expectedPlace1.title) {
                verifyPopupContent(expectedPlace1);
              } else if (title === expectedPlace2.title) {
                verifyPopupContent(expectedPlace2);
              }
            });
        });

      cy.get('.leaflet-popup-close-button').should('exist').then(($button) => {
        cy.wrap($button).click();
        cy.wait(500);
      })
    });
  });
});
