describe('Popup Tests on Mobile', () => {
  const viewports = ['iphone-x', 'iphone-6', 'ipad-2', 'samsung-s10']
  beforeEach(() => {
    cy.visit('/');
    cy.wait(1000);
  });

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
  };
  const expectedPlace2 = {
    title: "Zwierzyniecka",
    subtitle: "small bridge",
    categories: [
      ["type_of_place", "small bridge"],
      ["accessible_by", "bikes, pedestrians"]
    ]
  };

  viewports.forEach((viewport) => {

    it(`displays title and subtitle in the popup on ${viewport}`, () => {
      cy.viewport(viewport);
      cy.window().then((win) => {
        cy.stub(win, 'open').as('openStub');
      });

      const zoomInTimes = 1;
      for (let i = 0; i < zoomInTimes; i++) {
        cy.get('.leaflet-marker-icon').first().click({ force: true }); // Force click for mobile
        cy.wait(500);
      }

      // TODO - Find a way to search for a specific point, not iterate over all of them
      cy.get('.leaflet-marker-icon').each(($marker) => {
        cy.wrap($marker).click({ force: true }); // Force click for mobile
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
                cy.contains('button', expectedContent.CTA.displayValue).click({ force: true });
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

        cy.contains('report a problem').should('exist').click();

          // Verify the form appears
          cy.get('form').should('exist').within(() => {
            // Verify dropdown options
            cy.get('select').should('exist').within(() => {
              cy.get('option').then((options) => {
                const optionValues = [...options].map(option => option.value);
                expect(optionValues).to.include.members([
                  '',
                  'reportNotHere',
                  'reportOverload',
                  'reportBroken',
                  'reportOther',
                ]);
              });
            });

            // Select a problem type and verify behavior
            cy.get('select').select('reportOther'); // Assuming "Other" is localized correctly
            cy.get('input[name="problem"]').should('exist'); // Text input for "Other"

            // Fill out the form
            cy.get('input[name="problem"]').type('Custom issue description');
            cy.get('input[type="submit"]').should('exist').click();
          });

          // Verify the success message
          cy.get('form').should('not.exist'); // Form should no longer be visible
          cy.contains('p', /thank you/i).should('exist'); // Adjust message as per actual text

        cy.get('.leaflet-popup-close-button').should('exist').then(($button) => {
          cy.wrap($button).click({ force: true });
          cy.wait(500);
        });
      });
      });
  });

});
